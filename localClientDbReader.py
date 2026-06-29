import asyncio
import json
import logging
import os
import sqlite3
import sys
import time
import queue
from typing import List, Optional

from galaxy.api.consts import LicenseType, LocalGameState
from galaxy.api.types import LocalGame, Game, LicenseInfo, GameTime

if sys.platform.startswith("darwin"):
    ITCH_DB_PATH = os.path.expanduser("~/Library/Application Support/itch/db/butler.db")
else:
    ITCH_DB_PATH = os.path.join(os.getenv("appdata"), "itch/db/butler.db")


class localClientDbReader():
    def __init__(self):
        self.authenticated = False

        self.itch_db = None
        self.itch_db_cursor = None

        self.checking_for_new_games = False

        self.mylocal_game_ids = []
        
        self.updateQueue_add_game = queue.Queue()
        self.updateQueue_remove_game = queue.Queue()
        self.my_queue_update_local_game_status = queue.Queue()

        # Callbacks provided by the plugin.
        self._persistent_cache = None
        self._update_game_time = None
        self._push_cache = None

    def set_plugin_callbacks(self, persistent_cache, update_game_time, push_cache):
        """Wire plugin-level callbacks used for cache and playtime updates."""
        self._persistent_cache = persistent_cache
        self._update_game_time = update_game_time
        self._push_cache = push_cache

    async def get_owned_games(self) -> List[Game]:
        return await self.get_games()

    async def get_games(self):
        logging.debug("Opening connection to itch butler.db")
        self.itch_db = sqlite3.connect(ITCH_DB_PATH)
        self.itch_db_cursor = self.itch_db.cursor()
        resp = list(self.itch_db_cursor.execute("SELECT * FROM games WHERE classification = 'game'"))
        downloaded = [x[0] for x in list(self.itch_db_cursor.execute("SELECT game_id FROM caves"))]
        self.itch_db.close()
        logging.debug("Closing connection to itch butler.db")

        games = []

        logging.debug("Starting building games...")

        for game in resp:
            logging.debug(f"Building game {game[0]} ({game[2]})")
            if game[0] not in downloaded:
                logging.debug(f"Game {game[0]} ({game[2]}) seems to be only cached, skipping...")
                continue
            can_be_bought = True if game[11] == 1 else False
            min_price = game[10]
            license_type = LicenseType.FreeToPlay
            if can_be_bought and min_price > 0:
                license_type = LicenseType.SinglePurchase
            games.append(Game(game_id=game[0], game_title=game[2], dlcs=None, license_info=LicenseInfo(license_type)))
            logging.debug(f"Built {game[0]} ({game[2]})")

        self.mylocal_game_ids = [x.game_id for x in games]

        logging.debug("Finished building games")

        return games

    async def check_for_new_games(self):
        logging.debug("Checking for changes in the itch butler.db")
        self.checking_for_new_games = True
        games_before = self.mylocal_game_ids[:]
        games_after = await self.get_games()
        ids_after = [x.game_id for x in games_after]
        for game in games_after:
            if game.game_id not in games_before:
                self.updateQueue_add_game.put(game)
                self.my_queue_update_local_game_status.put(LocalGame(game_id=game.game_id, local_game_state=LocalGameState.Installed))
                logging.debug(f"Game {game.game_id} ({game.game_title}) is new, adding to galaxy...")

        for game in games_before:
            if game not in ids_after:
                self.updateQueue_remove_game.put(game)
                logging.debug(f"Game {game} seems to be uninstalled, removing from galaxy...")

        self.checking_for_new_games = False

        logging.debug("Finished checking for changes in the itch butler.db")

    async def get_local_games(self) -> List[LocalGame]:
        games = await self.get_games()
        local_games = []
        for game in games:
            local_games.append(LocalGame(game_id=game.game_id, local_game_state=LocalGameState.Installed))
        return local_games

    async def launch_game(self, game_id: str) -> None:
        logging.debug("query db")
        self.itch_db = sqlite3.connect(ITCH_DB_PATH)
        self.itch_db_cursor = self.itch_db.cursor()
        result = list(self.itch_db_cursor.execute("SELECT verdict FROM caves WHERE game_id=? LIMIT 1", [game_id]))
        self.itch_db.close()

        if not result:
            logging.error(f"No cave found for game_id {game_id}")
            return

        resp = json.loads(result[0][0])

        logging.info("building launch command")
        start = int(time.time())
        logging.info(resp["basePath"])
        logging.info(resp["candidates"][0]["path"])
        
        my_full_path = os.path.normpath(os.path.join(resp["basePath"], resp["candidates"][0]["path"]))
        my_base_path = os.path.dirname(my_full_path)
        
        logging.info(f"Launch path: {my_full_path}")
        logging.info(f"Working dir: {my_base_path}")
        
        # Mark the game as running in Galaxy while the process is active.
        self.my_queue_update_local_game_status.put(
            LocalGame(game_id=game_id, local_game_state=LocalGameState.Installed | LocalGameState.Running)
        )

        proc = await asyncio.create_subprocess_shell(
            f'"{my_full_path}"', 
            cwd=my_base_path
        )

        await proc.communicate()  # Wait for the process to exit.
        end = int(time.time())

        # Mark the game as stopped in Galaxy after the process exits.
        self.my_queue_update_local_game_status.put(
            LocalGame(game_id=game_id, local_game_state=LocalGameState.Installed)
        )

        # Round the elapsed playtime to the nearest minute before saving it.
        session_mins_played = round((end - start) / 60)

        if self._persistent_cache is not None and self._update_game_time is not None and self._push_cache is not None:
            time_played_key = f'time{game_id}'
            last_played_key = f'last{game_id}'
            time_played = (int(self._persistent_cache.get(time_played_key, 0))) + session_mins_played
            game_time = GameTime(game_id=game_id, time_played=time_played, last_played_time=end)
            self._update_game_time(game_time)
            self._persistent_cache[time_played_key] = str(time_played)
            self._persistent_cache[last_played_key] = str(end)
            self._push_cache()
        else:
            logging.warning("Plugin callbacks not set, game time not saved.")

    async def get_game_time(self, game_id: str, context: None) -> GameTime:
        return GameTime(
            game_id=game_id,
            time_played=None,
            last_played_time=None,
        )