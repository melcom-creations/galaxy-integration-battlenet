"""Short-lived OAuth callback bound only to this computer."""

import asyncio
import re
import secrets
from urllib.parse import parse_qs, urlsplit

from aiohttp import web

from consts import REDIRECT_URI


class CallbackError(ValueError):
    pass


class CallbackRejected(CallbackError):
    def __init__(self, reason):
        super().__init__("Battle.net authorization could not be completed")
        self.reason = reason


def callback_code(uri: str, expected_state: str) -> str:
    """Validate the complete callback before exposing its authorization code."""
    try:
        actual = urlsplit(uri)
        expected = urlsplit(REDIRECT_URI)
        if (actual.scheme, actual.netloc, actual.path) != (expected.scheme, expected.netloc, expected.path):
            raise CallbackError("Unexpected Battle.net callback address")
        if actual.fragment or len(uri) > 8192:
            raise CallbackError("Invalid Battle.net callback")
        query = parse_qs(actual.query, keep_blank_values=True, max_num_fields=16)
        states = query.get("state", [])
        if (not expected_state or len(states) != 1
                or not secrets.compare_digest(states[0].encode(), expected_state.encode())):
            raise CallbackError("Battle.net login session does not match; please reconnect")
        if "error" in query:
            errors = query['error']
            if len(errors) != 1 or not errors[0] or 'code' in query:
                raise CallbackError("Invalid Battle.net error response")
            raise CallbackRejected(errors[0])
        codes = query.get("code", [])
        if len(codes) != 1 or not codes[0] or any(c.isspace() for c in codes[0]):
            raise CallbackError("Missing or invalid Battle.net authorization code")
        return codes[0]
    except (TypeError, ValueError) as error:
        if isinstance(error, CallbackError):
            raise
        raise CallbackError("Invalid Battle.net callback") from None


class LocalOAuthCallbackServer:
    def __init__(self):
        self._runner = None
        self._expiry = None
        self.state = None
        self._received_code = None

    @property
    def end_uri_regex(self):
        return "^" + re.escape(REDIRECT_URI) + r"\?[^#]*$"

    async def start(self, state: str, timeout: float = 600):
        await self.stop()
        target = urlsplit(REDIRECT_URI)
        app = web.Application(client_max_size=8192)
        app.router.add_get(target.path, self._handle_callback)
        self._runner = web.AppRunner(app, access_log=None)
        try:
            await self._runner.setup()
            site = web.TCPSite(self._runner, target.hostname, target.port)
            await site.start()
        except BaseException:
            await self.stop()
            raise
        self.state = state
        self._expiry = asyncio.create_task(self._expire(timeout))

    async def _expire(self, timeout):
        await asyncio.sleep(timeout)
        await self.stop()

    async def stop(self):
        expiry, self._expiry = self._expiry, None
        if expiry is not None and expiry is not asyncio.current_task():
            expiry.cancel()
        self.state = None
        self._received_code = None
        runner, self._runner = self._runner, None
        if runner is not None:
            await runner.cleanup()

    def validate(self, uri):
        code = callback_code(uri, self.state)
        if self._received_code is not None and code != self._received_code:
            raise CallbackError("Battle.net callback was already received")
        return code

    async def _handle_callback(self, request):
        if request.remote != "127.0.0.1" or request.host != urlsplit(REDIRECT_URI).netloc:
            raise web.HTTPForbidden()
        headers = {"Cache-Control": "no-store", "Pragma": "no-cache",
                   "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff",
                   "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'"}
        try:
            self._received_code = self.validate(REDIRECT_URI + "?" + request.rel_url.raw_query_string)
        except CallbackError:
            return web.Response(status=400, text="Invalid or expired login. Please reconnect in GOG Galaxy.", headers=headers)
        return web.Response(text="Login received. Return to GOG Galaxy to continue.", headers=headers)
