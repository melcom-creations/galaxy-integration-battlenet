import os
import asyncio
import logging as log
import subprocess
import abc
from time import time
from pathlib import Path
from typing import Dict, Optional

from process import ProcessProvider
from consts import Platform, SYSTEM, CONFIG_PATH, AGENT_PATH
from watcher import FileWatcher
from parsers import ConfigParser, DatabaseParser

from local_games import LocalGames, InstalledGame
import json
import errno


class ClientNotInstalledError(Exception):
    def __init__(self, message="Battle.net not installed", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


def load_product_db(product_db_path):
    with open(product_db_path, 'rb') as f:
        pdb = f.read()
    return pdb


def load_config(battlenet_config_path):
    with open(battlenet_config_path, 'rb') as f:
        config = json.load(f)
    return config


class BaseLocalClient(abc.ABC):

    PRODUCT_DB_PATH = Path(AGENT_PATH) / 'product.db'
    CONFIG_PATH = CONFIG_PATH

    def __init__(self, update_statuses):
        self._update_statuses = update_statuses
        self._process_provider = ProcessProvider()
        self._process = None
        self._exe: Optional[str] = self._find_exe()
        self._games_provider = LocalGames()

        self.database_parser: Optional[DatabaseParser] = None
        self.config_parser = ConfigParser(None)
        self.uninstaller = None
        self.installed_games_cache = self.get_installed_games()

        self.classic_games_parsing_task = None

    @property
    @abc.abstractmethod
    def is_installed(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def _find_exe(self) -> Optional[str]:
        """Returns Battlenet main executable"""
        raise NotImplementedError

    @abc.abstractmethod
    def _is_main_window_open(self) -> bool:
        """Return True if Blizzard main renderer window is present (main window, not login)"""
        raise NotImplementedError

    @abc.abstractmethod
    def _check_for_game_process(self, game: InstalledGame) -> bool:
        """Returns True if process matching game if found"""
        raise NotImplementedError

    def refresh(self):
        self._exe = self._find_exe()

    def _require_executable(self) -> str:
        if not self._exe:
            raise ClientNotInstalledError()
        return self._exe

    def is_running(self):
        if self._process and self._process.is_running():
            return True
        executable = self._exe
        if not executable:
            return False
        self._process = self._process_provider.get_process_by_path(executable)
        return bool(self._process)

    async def _prepare_to_launch(self, uid, timeout):
        """launches the client and waits till proper renderer is opened
        :param uid      str of game uid. Makes login window game oriented
        :param timeout  timestamp when a watch should be stopped
        """
        if self.is_running() and self._is_main_window_open():
            return

        executable = self._require_executable()
        subprocess.Popen([executable, f'--game={uid}'], cwd=os.path.dirname(executable))
        while time() < timeout:
            if self._is_main_window_open():
                log.debug('Preparing to launch ended {:.2f}s before timeout'.format(timeout - time()))
                return
            await asyncio.sleep(0.2)
        raise TimeoutError(f'Timeout reached when waiting for gameview from Battle.net')

    def install_game(self, uid: str):
        if not self.is_installed:
            raise ClientNotInstalledError()
        executable = self._require_executable()
        args = [
            executable,
            "--install",
            f"--game={uid}"
        ]
        subprocess.Popen(args, cwd=os.path.dirname(executable))

    def open_battlenet(self, uid: Optional[str] = None):
        if not self.is_installed:
            raise ClientNotInstalledError()
        executable = self._require_executable()
        if uid is not None:
            args = (executable, f"--game={uid}")
        else:
            args = (executable,)
        subprocess.Popen(args, cwd=os.path.dirname(executable))

    async def wait_until_game_stops(self, game: InstalledGame):
        if not self.is_running():
            return 'Client not running'
        process = self._process
        if process is None:
            return 'Client process not found'
        for child in process.children():
            if child.exe() in game.execs:
                game_process = child
                break
        else:
            return 'No subprocess matches'
        while True:
            if not game_process.is_running():
                return 'Game process is no longer running'
            await asyncio.sleep(1)

    async def launch_game(self, game: InstalledGame, wait_sec):
        if not self.is_installed:
            raise ClientNotInstalledError()
        timeout = time() + wait_sec

        if game.info.family == 'WoW_wow_classic':
            if SYSTEM == Platform.WINDOWS:
                cmd = f"\"{Path(game.install_path)/'World of Warcraft Launcher.exe'}\" --productcode=wow_classic"
            else:
                cmd = f"open \"{Path(game.install_path)/'World of Warcraft Launcher.app'}\" --args productcode=wow_classic"
            subprocess.Popen(cmd, shell=True)
        else:
            await self._prepare_to_launch(game.info.uid, timeout)
            executable = self._require_executable()
            cmd = f'"{executable}" --exec="launch {game.info.family}"'
            subprocess.Popen(cmd, cwd=os.path.dirname(executable), shell=True)
        log.info(f"Launch game and start waiting for game process")
        while time() < timeout:
            if self._check_for_game_process(game):
                return
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Game process has not appear within {wait_sec}s")

    def _load_local_files(self):
        try:
            product_db = load_product_db(self.PRODUCT_DB_PATH)
            self.database_parser = DatabaseParser(product_db)
        except FileNotFoundError as e:
            log.warning(f"product.db not found: {repr(e)}")
            return False
        except OSError as e:
            if e.errno == errno.EACCES or getattr(e, 'winerror', None) == 5:
                log.warning(f"product.db not accessible: {repr(e)}")
                self.config_parser = ConfigParser(None)
                return False
            raise
        else:
            database_parser = self.database_parser
            if database_parser is None:
                return False
            if self.is_installed != database_parser.battlenet_present:
                self.refresh()

        try:
            config = load_config(self.CONFIG_PATH)
            self.config_parser = ConfigParser(config)
        except FileNotFoundError as e:
            log.warning(f"config file not found: {repr(e)}")
            self.config_parser = ConfigParser(None)
            return False
        except OSError as e:
            if e.errno == errno.EACCES or getattr(e, 'winerror', None) == 5:
                log.warning(f"config file not accessible: {repr(e)}")
                self.config_parser = ConfigParser(None)
                return False
            raise
        return True

    async def register_local_data_watcher(self):
        parse_local_data_event = asyncio.Event()
        FileWatcher(self.CONFIG_PATH, parse_local_data_event, interval=1)
        FileWatcher(self.PRODUCT_DB_PATH, parse_local_data_event, interval=2.5)
        parse_local_data_event.set()
        while True:
            try:
                await parse_local_data_event.wait()

                if not self._load_local_files():
                    continue
                database_parser = self.database_parser
                if database_parser is None:
                    continue
                if self.is_installed != database_parser.battlenet_present:
                    self.refresh()

                await asyncio.to_thread(
                    self._games_provider.parse_local_battlenet_games,
                    database_parser.games,
                    self.config_parser.games,
                )
                refreshed_games = self.get_installed_games()

                self._update_statuses(refreshed_games, self.installed_games_cache)
                self.installed_games_cache = refreshed_games
            except Exception:
                log.exception("Unexpected error while processing local Battle.net updates")
            finally:
                parse_local_data_event.clear()

    async def register_classic_games_updater(self):
        tick_count = 0
        while True:
            try:
                tick_count += 1
                if tick_count % 30 == 0:
                    if not self.classic_games_parsing_task or self.classic_games_parsing_task.done():
                        self.classic_games_parsing_task = asyncio.create_task(self._safe_parse_local_classic_games())
                        refreshed_games = self.get_installed_games()
                        self._update_statuses(refreshed_games, self.installed_games_cache)
                        self.installed_games_cache = refreshed_games
            except Exception:
                log.exception("Unexpected error while updating classic Battle.net games")
            await asyncio.sleep(1)

    async def _safe_parse_local_classic_games(self):
        try:
            await self._games_provider.parse_local_classic_games()
        except Exception:
            log.exception("Classic Battle.net game scan failed")

    def games_finished_parsing(self):
        return self._games_provider.parsed_classics and self._games_provider.parsed_battlenet

    def get_installed_games(self, timeout=1) -> Dict[str, InstalledGame]:
        games = {}

        if self._games_provider.installed_battlenet_games_lock.acquire(True, timeout):
            try:
                games = dict(self._games_provider.installed_battlenet_games)
            finally:
                self._games_provider.installed_battlenet_games_lock.release()

        if self._games_provider.installed_classic_games_lock.acquire(True, timeout):
            try:
                games = {**games, **dict(self._games_provider.installed_classic_games)}
            finally:
                self._games_provider.installed_classic_games_lock.release()

        return games

    def get_running_games(self):
        return ProcessProvider().update_games_processes(self.get_installed_games().values())
