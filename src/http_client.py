from definitions import WebsiteAuthData
import pickle
import asyncio
import secrets
import json
import re

import requests
import requests.cookies
from urllib.parse import urlencode, urlsplit, urljoin
from typing import Any, Dict, Optional

from galaxy.api.errors import InvalidCredentials, BackendTimeout, NetworkError
from galaxy.api.types import Authentication, NextStep

from consts import REDIRECT_URI, FIREFOX_AGENT
from oauth_config import OAuthCredentials
from oauth_callback import CallbackError, CallbackRejected, LocalOAuthCallbackServer, callback_code
from region_helper import _found_region, guess_region


class AuthenticatedHttpClient(object):
    def __init__(self, plugin, oauth_credentials: OAuthCredentials | None = None):
        self._plugin = plugin
        self._oauth_credentials = oauth_credentials
        self.user_details: Optional[Dict[str, Any]] = None
        self._region: Optional[str] = None
        self.session: Optional[requests.Session] = None
        self.creds: Optional[Dict[str, Any]] = None
        self.timeout = 40.0
        self.attempted_to_set_battle_tag = None
        self.auth_data: Optional[WebsiteAuthData] = None
        self._oauth_state = None
        self.callback_server = LocalOAuthCallbackServer()
        self._refresh_lock = asyncio.Lock()

    def set_oauth_credentials(self, credentials: OAuthCredentials) -> None:
        self._oauth_credentials = credentials

    def _require_oauth_credentials(self) -> OAuthCredentials:
        if self._oauth_credentials is None:
            raise InvalidCredentials("Battle.net OAuth credentials are not configured")
        return self._oauth_credentials

    def is_authenticated(self):
        return self.session is not None

    def _require_session(self) -> requests.Session:
        if self.session is None:
            raise InvalidCredentials()
        return self.session

    def _require_auth_data(self) -> WebsiteAuthData:
        if self.auth_data is None:
            raise InvalidCredentials()
        return self.auth_data

    def _require_user_details(self) -> Dict[str, Any]:
        if self.user_details is None:
            raise InvalidCredentials()
        return self.user_details

    def _require_creds(self) -> Dict[str, Any]:
        if self.creds is None:
            raise InvalidCredentials()
        return self.creds

    async def shutdown(self):
        self._oauth_state = None
        await self.callback_server.stop()
        if self.session:
            self.session.close()
            self.session = None

    def process_stored_credentials(self, stored_credentials):
        auth_data = WebsiteAuthData(
            cookie_jar=pickle.loads(bytes.fromhex(stored_credentials['cookie_jar'])),
            access_token=stored_credentials['access_token'],
            region=stored_credentials['region'] if 'region' in stored_credentials else 'eu'
        )
        self.auth_data = auth_data

        # Load the cached user details when available.
        if 'user_details_cache' in stored_credentials:
            self.user_details = stored_credentials['user_details_cache']
        return auth_data

    async def get_auth_data_login(self, cookie_jar, credentials):
        try:
            code = self.callback_server.validate(credentials.get('end_uri', ''))
        except CallbackRejected:
            raise
        except CallbackError as error:
            raise InvalidCredentials(str(error)) from None
        finally:
            self._oauth_state = None
            await self.callback_server.stop()
        access_token = await asyncio.get_running_loop().run_in_executor(
            None, self._exchange_code, code)
        self.auth_data = WebsiteAuthData(cookie_jar=cookie_jar, access_token=access_token, region=self.region)
        return self.auth_data

    def _exchange_code(self, code):
        oauth_credentials = self._require_oauth_credentials()
        data = {
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "client_id": oauth_credentials.client_id,
            "client_secret": oauth_credentials.client_secret,
            "code": code
        }
        try:
            with requests.Session() as session:
                response = session.post(f"{self.blizzard_oauth_url}/token", data=data,
                                        timeout=self.timeout, allow_redirects=False)
                if response.status_code != 200:
                    raise InvalidCredentials("Battle.net login could not be completed; check the registered local Redirect URL")
                result = response.json()
                token = result.get('access_token') if isinstance(result, dict) else None
                if not isinstance(token, str) or not token:
                    raise InvalidCredentials("Battle.net did not return an access token")
                return token
        except requests.Timeout:
            raise BackendTimeout() from None
        except requests.RequestException:
            raise NetworkError() from None
        except ValueError:
            raise InvalidCredentials("Invalid Battle.net token response") from None

    async def refresh_access_token_with_cookies(self) -> str:
        """Follow only Blizzard HTTPS redirects; consume the local callback without requesting it."""
        if self._require_oauth_credentials().redirect_uri != REDIRECT_URI:
            raise InvalidCredentials("Reconnect to configure the local Battle.net callback")
        async with self._refresh_lock:
            state = secrets.token_urlsafe(32)
            code = await asyncio.get_running_loop().run_in_executor(None, self._refresh_code, state)
            new_token = await asyncio.get_running_loop().run_in_executor(None, self._exchange_code, code)
            self._require_auth_data().access_token = new_token
            self._require_session().headers["Authorization"] = f"Bearer {new_token}"
            self.refresh_credentials()
            return new_token

    def _refresh_code(self, state):
        url = self._authorization_url(state)
        allowed_hosts = {urlsplit(self.blizzard_oauth_url).hostname,
                         urlsplit(self.blizzard_accounts_url).hostname,
                         urlsplit(self.blizzard_battlenet_login_url).hostname}
        if self.region != 'cn':
            allowed_hosts.update({'oauth.battle.net', 'account.battle.net', 'account.blizzard.com'})
        try:
            with requests.Session() as session:
                session.cookies.update(self._require_session().cookies)
                session.headers['User-Agent'] = FIREFOX_AGENT
                for _ in range(10):
                    parsed = urlsplit(url)
                    if (parsed.scheme != 'https' or parsed.hostname not in allowed_hosts
                            or parsed.port not in (None, 443) or parsed.username or parsed.password):
                        raise InvalidCredentials("Unexpected Battle.net login redirect; please reconnect")
                    response = session.get(url, allow_redirects=False, timeout=self.timeout)
                    if response.status_code not in (301, 302, 303, 307, 308):
                        raise InvalidCredentials("Battle.net requires an interactive login; please reconnect")
                    location = response.headers.get('Location')
                    if not location:
                        raise InvalidCredentials("Missing Battle.net login redirect")
                    url = urljoin(url, location)
                    if urlsplit(url).hostname == '127.0.0.1':
                        return callback_code(url, state)
        except requests.Timeout:
            raise BackendTimeout() from None
        except requests.RequestException:
            raise NetworkError() from None
        except ValueError:
            raise InvalidCredentials("Invalid Battle.net login redirect; please reconnect") from None
        raise InvalidCredentials("Battle.net login redirect limit reached; please reconnect")

    def validate_auth_status(self, auth_status):
        # Cached profile data is not evidence that a login is still valid.
        if (not isinstance(auth_status, dict) or 'error' in auth_status
                or 'IS_AUTHENTICATED_FULLY' not in auth_status.get('authorities', [])):
            raise InvalidCredentials()
        return True

    def parse_user_details(self):
        user_details = self._require_user_details()
        if "id" not in user_details or "battletag" not in user_details:
            raise InvalidCredentials()
        return Authentication(user_details["id"], user_details["battletag"])

    def _authorization_url(self, state):
        oauth_credentials = self._require_oauth_credentials()
        return f'{self.blizzard_oauth_url}/authorize?' + urlencode({
            'response_type': 'code', 'client_id': oauth_credentials.client_id,
            'redirect_uri': REDIRECT_URI, 'scope': 'wow.profile sc2.profile', 'state': state})

    async def authenticate_using_login(self):
        if self._require_oauth_credentials().redirect_uri != REDIRECT_URI:
            raise InvalidCredentials("Configure the local Battle.net callback first")
        self.attempted_to_set_battle_tag = False
        self._oauth_state = secrets.token_urlsafe(32)
        try:
            await self.callback_server.start(self._oauth_state)
        except OSError:
            self._oauth_state = None
            raise InvalidCredentials("Local login port 43821 is unavailable. Close other Battle.net integration login windows and try again.") from None
        auth_params = {
            "window_title": "Login to Battle.net",
            "window_width": 540,
            "window_height": 700,
            "start_uri": self._authorization_url(self._oauth_state),
            "end_uri_regex": self.callback_server.end_uri_regex
        }
        error_uri = REDIRECT_URI + '?' + urlencode({
            'state': self._oauth_state, 'error': 'invalid_redirect_uri'})
        # Read only the known error message, never login fields or cookies.
        script = r"""(function () {
            if (window.__galaxyCallbackErrorWatcher) return;
            window.__galaxyCallbackErrorWatcher = true;
            var finished = false;
            function inspect() {
                if (finished || !document.body) return;
                var message = (document.body.innerText || '').replace(/\s+/g, ' ').toLowerCase();
                if (message.indexOf('invalid grant type or callback url is not valid') !== -1) {
                    finished = true;
                    window.location.replace(__ERROR_URI__);
                }
            }
            inspect();
            if (!finished) {
                var watcher = new MutationObserver(inspect);
                watcher.observe(document.documentElement, {childList: true, subtree: true, characterData: true});
                window.setTimeout(function () { watcher.disconnect(); }, 600000);
            }
        })();""".replace('__ERROR_URI__', json.dumps(error_uri))
        origins = {self.blizzard_oauth_url.split('/oauth')[0], self.blizzard_accounts_url}
        if self.region != 'cn':
            origins.update({'https://oauth.battle.net', 'https://account.battle.net', 'https://account.blizzard.com'})
        scripts = {'^' + re.escape(origin) + r'(?::443)?/': [script] for origin in origins}
        return NextStep("web_session", auth_params, js=scripts)

    def parse_auth_after_setting_battletag(self):
        creds = self._require_creds()
        user_details = self._require_user_details()
        creds["user_details_cache"] = user_details
        try:
            battletag = user_details["battletag"]
        except KeyError:
            raise InvalidCredentials()
        self._plugin.store_credentials(creds)
        return Authentication(user_details["id"], battletag)

    def parse_cookies(self, cookies):
        if not self.region:
            self.region = _found_region(cookies)
        new_cookies = {cookie["name"]: cookie["value"] for cookie in cookies}
        return requests.cookies.cookiejar_from_dict(new_cookies)

    def set_credentials(self):
        auth_data = self._require_auth_data()
        self.creds = {"cookie_jar": pickle.dumps(auth_data.cookie_jar).hex(), "access_token": auth_data.access_token,
                      "user_details_cache": self.user_details, "region": auth_data.region}

    def parse_battletag(self):
        user_details = self.user_details
        if not user_details or "battletag" not in user_details:
            auth_data = self._require_auth_data()
            st_parameter = requests.utils.dict_from_cookiejar(auth_data.cookie_jar).get("BA-tassadar")
            if not st_parameter:
                raise InvalidCredentials()
            start_uri = f'{self.blizzard_battlenet_login_url}/flow/' \
                             f'app.app?step=login&ST={st_parameter}&app=app&cr=true'
            auth_params = {
                "window_title": "Login to Battle.net",
                "window_width": 540,
                "window_height": 700,
                "start_uri": start_uri,
                "end_uri_regex": r".*accountName.*"
            }
            self.attempted_to_set_battle_tag = True
            return NextStep("web_session", auth_params)

        creds = self._require_creds()
        self._plugin.store_credentials(creds)
        return Authentication(user_details["id"], user_details["battletag"])

    async def create_session(self):
        auth_data = self._require_auth_data()
        session = requests.Session()
        session.cookies = auth_data.cookie_jar
        self.region = auth_data.region
        session.max_redirects = 300
        session.headers.update({
            "Authorization": f"Bearer {auth_data.access_token}",
            "User-Agent": FIREFOX_AGENT
        })
        self.session = session

    def refresh_credentials(self):
        session = self._require_session()
        auth_data = self._require_auth_data()
        creds = {
            "cookie_jar": pickle.dumps(session.cookies).hex(),
            "access_token": auth_data.access_token,
            "region": auth_data.region,
            "user_details_cache": self.user_details
        }
        self._plugin.store_credentials(creds)

    @property
    def region(self) -> str:
        region = self._region
        if not isinstance(region, str) or not region:
            guessed_region = guess_region(self._plugin.local_client)
            region = guessed_region if isinstance(guessed_region, str) and guessed_region else 'eu'
            self._region = region
        return region

    @region.setter
    def region(self, value: str) -> None:
        self._region = value

    @property
    def blizzard_accounts_url(self):
        if self.region == 'cn':
            return "https://account.blizzardgames.cn"
        else:
            return f"https://{self.region}.account.blizzard.com"

    @property
    def blizzard_oauth_url(self):
        if self.region == 'cn':
            return "https://www.battlenet.com.cn/oauth"
        else:
            return f"https://{self.region}.battle.net/oauth"

    @property
    def blizzard_api_url(self):
        if self.region == 'cn':
            return "https://gateway.battlenet.com.cn"
        else:
            return f"https://{self.region}.api.blizzard.com"

    @property
    def blizzard_battlenet_download_url(self):
        if self.region == 'cn':
            return "https://cn.blizzard.com/zh-cn/apps/battle.net/desktop"
        else:
            return "https://www.blizzard.com/apps/battle.net/desktop"

    @property
    def blizzard_battlenet_login_url(self):
        if self.region == 'cn':
            return 'https://www.battlenet.com.cn/login/zh'
        else:
            return f'https://{self.region}.battle.net/login/en'
