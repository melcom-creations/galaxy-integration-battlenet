from definitions import WebsiteAuthData
import pickle
import asyncio
import secrets

import requests
import requests.cookies
from urllib.parse import urlparse, parse_qs
from functools import partial
from typing import Any, Dict, Optional

from galaxy.api.errors import InvalidCredentials
from galaxy.api.types import Authentication, NextStep

from consts import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, FIREFOX_AGENT
from region_helper import _found_region, guess_region


class AuthenticatedHttpClient(object):
    def __init__(self, plugin):
        self._plugin = plugin
        self.user_details: Optional[Dict[str, Any]] = None
        self._region: Optional[str] = None
        self.session: Optional[requests.Session] = None
        self.creds: Optional[Dict[str, Any]] = None
        self.timeout = 40.0
        self.attempted_to_set_battle_tag = None
        self.auth_data: Optional[WebsiteAuthData] = None
        self._oauth_state = None

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
        if self.session:
            self.session.close()
            self.session = None

    def process_stored_credentials(self, stored_credentials):
        auth_data = WebsiteAuthData(
            cookie_jar=pickle.loads(bytes.fromhex(stored_credentials['cookie_jar'])),
            access_token=stored_credentials['access_token'],
            region=stored_credentials['region'] if 'region' in stored_credentials else 'eu'
        )

        # Load the cached user details when available.
        if 'user_details_cache' in stored_credentials:
            self.user_details = stored_credentials['user_details_cache']
            self.auth_data = auth_data
        return auth_data

    async def get_auth_data_login(self, cookie_jar, credentials):
        code = parse_qs(urlparse(credentials['end_uri']).query)["code"][0]
        loop = asyncio.get_running_loop()

        s = requests.Session()
        url = f"{self.blizzard_oauth_url}/token"
        data = {
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code
        }
        response = await loop.run_in_executor(None, partial(s.post, url, data=data))
        response.raise_for_status()
        result = response.json()
        access_token = result["access_token"]
        self.auth_data = WebsiteAuthData(cookie_jar=cookie_jar, access_token=access_token, region=self.region)
        return self.auth_data

    async def refresh_access_token_with_cookies(self) -> str:
        """
        Silently intercepts the OAuth redirect chain using stored session cookies,
        extracts the fresh authorization code, and exchanges it for a new access token.
        This keeps the user logged in permanently across GOG Galaxy restarts.
        """
        loop = asyncio.get_running_loop()
        headers = {
            'User-Agent': FIREFOX_AGENT
        }
        url = f"{self.blizzard_accounts_url}:443/oauth2/authorization/account-settings"
        
        # Request the account settings page with the stored cookies.
        session = self._require_session()
        response = await loop.run_in_executor(
            None, 
            partial(session.get, url, headers=headers, allow_redirects=True, timeout=self.timeout)
        )
        
        # Inspect the redirect chain for the authorization code.
        code = None
        for resp in [response] + response.history:
            parsed = urlparse(resp.url)
            query = parse_qs(parsed.query)
            if "code" in query:
                code = query["code"][0]
                break
                
        if not code:
            raise InvalidCredentials("No authorization code found in cookie refresh flow")
            
        # Exchange the authorization code for an OAuth access token.
        token_url = f"{self.blizzard_oauth_url}/token"
        data = {
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code
        }
        
        token_response = await loop.run_in_executor(
            None, 
            partial(session.post, token_url, data=data, timeout=self.timeout)
        )
        token_response.raise_for_status()
        result = token_response.json()
        
        # Update the active session credentials after token refresh.
        new_token = result["access_token"]
        auth_data = self._require_auth_data()
        auth_data.access_token = new_token
        session.headers["Authorization"] = f"Bearer {new_token}"
        
        # Persist the refreshed credentials in GOG Galaxy storage.
        self.refresh_credentials()
        return new_token

    # Prefer live user data when the token remains valid.
    # Fall back to the stored usertag and name if token validation fails.
    
    def validate_auth_status(self, auth_status):
        if 'error' in auth_status:
            if not self.user_details:
                raise InvalidCredentials()
            else:
                return False
        elif not self.user_details:
            raise InvalidCredentials()
        else:
            if not ("authorities" in auth_status and "IS_AUTHENTICATED_FULLY" in auth_status["authorities"]):
                raise InvalidCredentials()
            return True

    def parse_user_details(self):
        user_details = self._require_user_details()
        if "id" not in user_details or "battletag" not in user_details:
            raise InvalidCredentials()
        return Authentication(user_details["id"], user_details["battletag"])

    def authenticate_using_login(self):
        self._oauth_state = secrets.token_hex(16)
        _URI = (
            f'{self.blizzard_oauth_url}/authorize'
            f'?response_type=code'
            f'&client_id={CLIENT_ID}'
            f'&redirect_uri={REDIRECT_URI}'
            f'&scope=wow.profile+sc2.profile'
            f'&state={self._oauth_state}'
        )
        auth_params = {
            "window_title": "Login to Battle.net",
            "window_width": 540,
            "window_height": 700,
            "start_uri": _URI,
            "end_uri_regex": r"(.*logout&app=oauth.*)|(^http://friendsofgalaxy\.com.*)"
        }
        return NextStep("web_session", auth_params)

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
