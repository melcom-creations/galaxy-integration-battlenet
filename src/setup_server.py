import html
import logging
import re
import secrets
from pathlib import Path
from typing import Optional

from aiohttp import web

from oauth_config import OAuthConfigError, OAuthCredentials, validate_credentials


logger = logging.getLogger(__name__)

FORM_PATH = "/"
SAVE_PATH = "/save"
COMPLETE_PATH = "/complete"


_COMPLETE_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Battle.net setup complete</title>
<style>body{font-family:"Segoe UI",system-ui,sans-serif;background:#0d1117;color:#e6edf3;
margin:0;padding:28px;}</style></head>
<body><h2>OAuth credentials accepted</h2>
<p>Waiting for GOG Galaxy to continue with the Battle.net login.</p></body></html>
"""


class LocalSetupServer:
    def __init__(self):
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._nonce: Optional[str] = None
        self.port: Optional[int] = None
        self.captured_credentials: Optional[OAuthCredentials] = None

    async def start(self) -> int:
        if self._runner is not None and self.port is not None:
            return self.port

        self._nonce = secrets.token_urlsafe(32)
        self.captured_credentials = None
        app = web.Application(client_max_size=8192)
        app.router.add_get(FORM_PATH, self._handle_form)
        app.router.add_post(SAVE_PATH, self._handle_save)
        app.router.add_get(COMPLETE_PATH, self._handle_complete)

        self._runner = web.AppRunner(app, access_log=None)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "127.0.0.1", 0)
        await self._site.start()
        sockets = self._site._server.sockets if self._site._server else []
        if len(sockets) != 1:
            await self.stop()
            raise OSError("Local Battle.net setup server did not bind exactly one socket")
        address = sockets[0].getsockname()
        if address[0] != "127.0.0.1":
            await self.stop()
            raise OSError("Local Battle.net setup server did not bind to IPv4 loopback")
        self.port = int(address[1])
        logger.info("Local Battle.net setup server listening on IPv4 loopback port %s", self.port)
        return self.port

    async def stop(self) -> None:
        self.captured_credentials = None
        if self._runner is not None:
            await self._runner.cleanup()
        self._runner = None
        self._site = None
        self._nonce = None
        self.port = None

    @property
    def base_url(self) -> str:
        if self.port is None:
            raise RuntimeError("Local Battle.net setup server is not running")
        return f"http://127.0.0.1:{self.port}/"

    @property
    def complete_url(self) -> str:
        if self.port is None:
            raise RuntimeError("Local Battle.net setup server is not running")
        return f"http://127.0.0.1:{self.port}{COMPLETE_PATH}"

    @property
    def end_uri_regex(self) -> str:
        return "^" + re.escape(self.complete_url) + "$"

    @staticmethod
    def _is_loopback_request(request: web.Request) -> bool:
        return request.remote == "127.0.0.1"

    @staticmethod
    def _response_headers() -> dict[str, str]:
        return {
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": (
                "default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src https://fonts.gstatic.com; script-src 'unsafe-inline'; "
                "connect-src 'self'; "
                "form-action 'self'; base-uri 'none'"
            ),
        }

    async def _handle_form(self, request: web.Request):
        if not self._is_loopback_request(request):
            raise web.HTTPForbidden()
        template_path = Path(__file__).parent / "setup.html"
        try:
            page = template_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise web.HTTPInternalServerError(text="The setup page could not be loaded") from error
        page = page.replace("__NONCE__", html.escape(self._nonce or "", quote=True))
        return web.Response(
            text=page,
            content_type="text/html",
            headers=self._response_headers(),
        )

    async def _handle_save(self, request: web.Request):
        if not self._is_loopback_request(request):
            raise web.HTTPForbidden()
        data = await request.post()
        submitted_nonce = data.get("nonce")
        if (
            not isinstance(submitted_nonce, str)
            or not self._nonce
            or not secrets.compare_digest(submitted_nonce, self._nonce)
        ):
            raise web.HTTPForbidden(text="Invalid setup session")
        try:
            self.captured_credentials = validate_credentials(
                data.get("client_id"),
                data.get("client_secret"),
            )
        except OAuthConfigError as error:
            return web.Response(
                text=str(error),
                content_type="text/plain",
                status=400,
                headers=self._response_headers(),
            )
        logger.info("Captured Battle.net OAuth credentials from the local setup form")
        raise web.HTTPSeeOther(self.complete_url, headers=self._response_headers())

    async def _handle_complete(self, request: web.Request):
        if not self._is_loopback_request(request):
            raise web.HTTPForbidden()
        if self.captured_credentials is None:
            raise web.HTTPConflict(text="Battle.net OAuth credentials were not captured")
        return web.Response(
            text=_COMPLETE_HTML,
            content_type="text/html",
            headers=self._response_headers(),
        )
