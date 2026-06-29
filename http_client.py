import logging
import aiohttp
from galaxy.api.errors import AuthenticationRequired
from galaxy.http import create_client_session


class HTTPClient(object):
    def __init__(self, store_credentials):
        self._store_credentials = store_credentials
        self._access_token = None
        self.session = create_client_session()

    def update_cookies(self, credentials):
        # Credentials may contain an access token or cookie data.
        if isinstance(credentials, dict) and "access_token" in credentials:
            self._access_token = credentials["access_token"]
            logging.info("HTTPClient: access_token set")
        else:
            # Use cookie-based authentication when no access token is available.
            logging.warning("HTTPClient: no access_token in credentials, got: %s", list(credentials.keys()) if credentials else None)

    async def get(self, url):
        logging.debug('HTTPClient.get: %s', url)
        headers = {}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        response = await self.session.get(url, headers=headers)
        parsed = await response.json()
        if response.status == 401:
            raise AuthenticationRequired()
        return parsed

    async def close(self):
        await self.session.close()
