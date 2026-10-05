import asyncio
import requests
import functools
import logging
import time

logging.getLogger("urllib3").setLevel(logging.WARNING)

from http import HTTPStatus

from galaxy.api.errors import (
    AccessDenied, AuthenticationRequired,
    BackendTimeout, BackendNotAvailable, BackendError, InvalidCredentials, NetworkError, UnknownError
)

from consts import FIREFOX_AGENT

class AccessTokenExpired(Exception):
    pass


class BackendClient(object):
    def __init__(self, plugin, authentication_client):
        self._plugin = plugin
        self._authentication_client = authentication_client
        self._account_lock = asyncio.Lock()
        self._account_retry_after = 0.0

    async def _authenticated_request(self, method, url, data=None, json=True, headers=None, ignore_failure=False):
        """
        Makes an authenticated request and retries once with a refreshed OAuth token after a 401 response.
        """
        try:
            return await self.do_request(method, url, data, json, headers, ignore_failure)
        except AuthenticationRequired:
            try:
                await self._authentication_client.refresh_access_token_with_cookies()
            except InvalidCredentials:
                raise AuthenticationRequired()
            return await self.do_request(method, url, data, json, headers, ignore_failure)

    @staticmethod
    def handle_status_code(status_code):
        if status_code == HTTPStatus.UNAUTHORIZED:
            raise AuthenticationRequired()
        if status_code == HTTPStatus.FORBIDDEN:
            raise AccessDenied()
        if status_code == HTTPStatus.SERVICE_UNAVAILABLE:
            raise BackendNotAvailable()
        if status_code >= 500:
            raise BackendError()
        if status_code >= 400:
            raise UnknownError()

    async def do_request(self, method, url, data=None, json=True, headers=None, ignore_failure=False):
        loop = asyncio.get_running_loop()
        if not headers:
            headers = self._authentication_client.session.headers
        try:
            if data is None:
                data = {}
            params = {
                "method": method,
                "url": url,
                "data": data,
                "timeout": self._authentication_client.timeout,
                "headers": headers
            }
            try:
                response = await loop.run_in_executor(None, functools.partial(self._authentication_client.session.request, **params))
            except (requests.Timeout, requests.ConnectTimeout, requests.ReadTimeout):
                logging.debug(f'Request to {url} timed out')
                raise BackendTimeout()
            except requests.ConnectionError:
                raise NetworkError

            if not ignore_failure:
                logging.debug(f'Request to {url} responsed with status code {response.status_code}')
                self.handle_status_code(response.status_code)

            if json:
                return response.json()
            else:
                return response

        except Exception as e:
            raise e

    async def refresh_cookies(self):
        """
        No-op: Silent cookie refresh is not supported with a custom OAuth client.
        """
        logging.debug("refresh_cookies() called - skipped (not supported with custom OAuth client)")

    async def get_user_info(self):
        url = f"{self._authentication_client.blizzard_oauth_url}/userinfo"
        return await self._authenticated_request("GET", url)

    async def get_account_details(self):
        details_url = f"{self._authentication_client.blizzard_accounts_url}/api/details"
        return await self.do_request("GET", details_url)

    async def get_owned_games(self):
        return await self._account_library_request('games-and-subs')

    async def get_owned_classic_games(self):
        return await self._account_library_request('classic-games')

    async def _account_library_request(self, endpoint):
        # Account website sessions are independent of the personal OAuth client.
        # A website 401 does not mean the plugin's access token has expired.
        client = self._authentication_client
        origin = (client.blizzard_accounts_url if client.region == 'cn'
                  else 'https://account.battle.net')
        headers = {'User-Agent': FIREFOX_AGENT, 'Authorization': None}
        url = f'{origin}/api/{endpoint}'
        async with self._account_lock:
            try:
                return await self.do_request('GET', url, headers=headers)
            except AuthenticationRequired:
                if client.region == 'cn' or time.monotonic() < self._account_retry_after:
                    raise
                # Bound retries when the website requires interactive login.
                self._account_retry_after = time.monotonic() + 300
                renewed = await asyncio.get_running_loop().run_in_executor(
                    None, client.refresh_account_website_session)
                if not renewed:
                    raise
                client.refresh_credentials()
                self._account_retry_after = 0.0
                logging.info('Battle.net account session restored automatically and saved.')
                return await self.do_request('GET', url, headers=headers)

    async def validate_access_token(self, access_token):
        token_url = f"{self._authentication_client.blizzard_oauth_url}/check_token"
        return await self.do_request("POST", token_url, data={"token": access_token}, ignore_failure=True)

    async def get_sc2_player_data(self, account_id):
        url = f"{self._authentication_client.blizzard_api_url}/sc2/player/{account_id}"
        return await self._authenticated_request("GET", url)

    async def get_sc2_profile_data(self, region_id, realm_id, player_id):
        url = f"{self._authentication_client.blizzard_api_url}/sc2/profile/{region_id}/{realm_id}/{player_id}"
        return await self._authenticated_request("GET", url)

    async def get_wow_character_data(self):
        url = f"{self._authentication_client.blizzard_api_url}/wow/user/characters"
        return await self._authenticated_request("GET", url)

    async def get_wow_character_achievements(self, realm, character_name):
        url = f"{self._authentication_client.blizzard_api_url}/wow/character/{realm.lower()}/{character_name}?fields=achievements"
        return await self.do_request("GET", url)

    async def get_ow_player_data(self):
        player_name = self._authentication_client.user_details['battletag']
        url = f"https://owapi.io/profile/pc/{self._authentication_client.region}/{player_name.replace('#', '-')}"
        return await self.do_request('GET', url)
