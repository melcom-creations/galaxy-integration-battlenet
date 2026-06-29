import os
import sys

# Add the bundled Modules directory to sys.path so local dependencies can be imported.
modules_dir = os.path.join(os.path.dirname(__file__), 'Modules')
if os.path.isdir(modules_dir) and modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

import json
import logging
from pathlib import Path

from typing import List, Optional
from datetime import datetime
import math
import time

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform, LicenseType, OSCompatibility
from galaxy.api.types import NextStep, Authentication, Game, LicenseInfo, LocalGame, GameTime
from galaxy.api.errors import AuthenticationRequired, AccessDenied, InvalidCredentials

from localClientDbReader import localClientDbReader
from http_client import HTTPClient

with open(Path(__file__).parent / 'manifest.json', 'r') as f:
    __version__ = json.load(f)['version']

CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'
SETUP_FILE = Path(__file__).parent / 'setup.html'
KEYS_URL = 'https://api.itch.io/profile/owned-keys?page=%s'
HOMEPAGE = 'https://www.itch.io'


class ItchIntegration(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(
            Platform.ItchIo,
            __version__,
            reader,
            writer,
            token
        )
        self.http_client = HTTPClient(self.store_credentials)
        self.session_cookie = None
        self.myLocalClientDbReader = localClientDbReader()

        self.myLocalClientDbReader.set_plugin_callbacks(
            self.persistent_cache,
            self.update_game_time,
            self.push_cache
        )

        self.time_last_update = datetime.now()
        self.my_handshook = False

    async def shutdown(self):
        await self.http_client.close()

    def _load_credentials_file(self):
        if not CREDENTIALS_FILE.exists():
            return None

        try:
            # UTF-8-SIG ignores a Windows BOM at the start of the file.
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8-sig') as f:
                credentials = json.load(f)
            if isinstance(credentials, dict):
                return credentials
            logging.warning("credentials.json does not contain a JSON object")
        except Exception as e:
            logging.warning(f"Could not read credentials.json: {e}")
        return None

    def _extract_access_token(self, credentials):
        if not isinstance(credentials, dict):
            return None

        token = credentials.get("access_token")
        if not isinstance(token, str):
            return None

        token = token.strip()
        return token or None

    def _setup_next_step(self):
        return NextStep(
            "web_session",
            {
                "window_title": "itch.io Plugin Setup",
                "window_width": 760,
                "window_height": 900,
                "start_uri": SETUP_FILE.as_uri(),
                "end_uri_regex": r"^$",
            },
        )

    async def authenticate(self, stored_credentials=None):
        logging.debug("authenticate")

        # 1. Prefer the local credentials.json file when it is available.
        file_credentials = self._load_credentials_file()
        access_token = self._extract_access_token(file_credentials)

        # 2. Use the Galaxy cache only when the file does not contain a token.
        if not access_token:
            credentials = stored_credentials if isinstance(stored_credentials, dict) else None
            access_token = self._extract_access_token(credentials)

        if not access_token:
            return self._setup_next_step()

        self.http_client.update_cookies({"access_token": access_token})
        try:
            user = await self.get_user_data()
            
            # Store the valid token back in the Galaxy cache.
            self.store_credentials({"access_token": access_token})
            
            return Authentication(str(user.get("id")), str(user.get("username")))
        except (AccessDenied, AuthenticationRequired):
            return self._setup_next_step()

    def _cookies_to_dict(self, cookies):
        session_cookies = {}
        for cookie in cookies or []:
            if isinstance(cookie, dict):
                name = cookie.get("name")
                value = cookie.get("value")
            else:
                name = getattr(cookie, "name", None)
                value = getattr(cookie, "value", None)

            if name and value is not None:
                session_cookies[name] = value
        return session_cookies

    async def pass_login_credentials(self, step, credentials, cookies):
        if isinstance(credentials, dict):
            access_token = self._extract_access_token(credentials)
            if access_token:
                self.http_client.update_cookies({"access_token": access_token})
            else:
                self.http_client.update_cookies(self._cookies_to_dict(cookies))
        else:
            self.http_client.update_cookies(self._cookies_to_dict(cookies))

        user = await self.get_user_data()
        logging.debug(user.get("id"))
        logging.debug(user.get("username"))
        return Authentication(str(user.get("id")), str(user.get("username")))

    def handshake_complete(self):
        logging.info("Handshake complete")
        self.my_handshook = True

    async def get_owned_games(self):
        whitelist = await load_whitelist_from_file()
        page = 1
        games = []
        while True:
            try:
                resp = await self.http_client.get(f"https://api.itch.io/profile/owned-keys?classification=game&page={page}")
            except AuthenticationRequired:
                self.lost_authentication()
                raise
            if len(resp.get("owned_keys")) == 0:
                return games
            self.parse_json_into_games(resp.get("owned_keys"), games, whitelist)
            page += 1
        return games

    async def get_user_data(self):
        resp = await self.http_client.get(f"https://api.itch.io/profile?")
        self.authenticated = True
        return resp.get("user")

    def parse_json_into_games(self, resp, games, whitelist):
        for key in resp:
            game = key.get("game")
            if not game.get("classification") == "game":
                continue
            game_name = game.get("title")
            game_num = str(game.get("id"))
            logging.debug('Parsed %s, %s', game_name, game_num)
            self.persistent_cache[game_num] = game
            this_game = Game(
                game_id=game_num,
                game_title=game_name,
                license_info=LicenseInfo(LicenseType.SinglePurchase),
                dlcs=[])
            if (len(whitelist) > 0):
                if (game_name in whitelist):
                    games.append(this_game)
            else:
                games.append(this_game)

    async def get_os_compatibility(self, game_id, context):
        try:
            compat = self.persistent_cache[str(game_id)].get("traits")
            os_compat = (
                (OSCompatibility.Windows if "p_windows" in compat else OSCompatibility(0)) |
                (OSCompatibility.MacOS if "p_osx" in compat else OSCompatibility(0)) |
                (OSCompatibility.Linux if "p_linux" in compat else OSCompatibility(0))
            )
            logging.debug("Compat value: %s", os_compat)
            if not os_compat == 0:
                return os_compat
        except KeyError:
            logging.error("Key not found in cache: %s", game_id)

    def tick(self) -> None:
        time_current = datetime.now()
        time_delta = (time_current - self.time_last_update)
        time_delta_seconds = time_delta.total_seconds()
        my_rounded_delta = math.floor(time_delta_seconds / 60)

        if my_rounded_delta > 0:
            self.create_task(self.myLocalClientDbReader.check_for_new_games(), "checkForNewGames")
            self.time_last_update = datetime.now()

        if (self.my_handshook):
            my_mod_delta = math.floor(time_delta_seconds / 7)
            my_counter = 0
            while my_mod_delta > 0 and my_counter < 101 and not self.myLocalClientDbReader.my_queue_update_local_game_status.empty():
                my_game_update_sending = self.myLocalClientDbReader.my_queue_update_local_game_status.get()
                logging.error(my_game_update_sending)
                self.update_local_game_status(my_game_update_sending)
                my_counter = my_counter + 1

    async def get_local_games(self) -> List[LocalGame]:
        logging.info("galaxy update local installed")
        return await self.myLocalClientDbReader.get_local_games()

    async def launch_game(self, game_id: str) -> None:
        logging.info("calling local launcher")
        await self.myLocalClientDbReader.launch_game(game_id)

    # Read the cached playtime and last-played timestamp from the local cache.
    async def get_game_time(self, game_id: str, context: None) -> GameTime:
        time_played_key = f'time{game_id}'
        last_played_key = f'last{game_id}'
        
        time_played = None
        last_played_time = None
        
        if time_played_key in self.persistent_cache:
            time_played = int(self.persistent_cache[time_played_key])
            
        if last_played_key in self.persistent_cache:
            last_played_time = int(self.persistent_cache[last_played_key])
            
        return GameTime(
            game_id=game_id,
            time_played=time_played,
            last_played_time=last_played_time,
        )


def main():
    create_and_run_plugin(ItchIntegration, sys.argv)


def log(msg):
    log_file = open(os.path.join(os.path.dirname(__file__), "log2.txt"), "a")
    log_file.write(str(msg) + "\n")
    log_file.close()

async def load_whitelist_from_file():
    ret = []
    if (os.path.isfile(Path(__file__).parent / 'whitelist.txt')):
        with open(Path(__file__).parent / 'whitelist.txt', 'r') as f:
            lines = f.readlines()
            for l in lines:
                ret.append(l.strip())
    return ret

if __name__ == "__main__":
    main()