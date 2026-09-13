import psutil
from typing import Set, Iterable
from local_games import InstalledGame
from definitions import ClassicGame


class ProcessProvider(object):
    def __init__(self):
        pass

    def get_process_by_path(self, path):
        for process in psutil.process_iter():
            try:
                if process.exe() != path:
                    continue
                parent = process.parent()
                if parent and parent.exe() == path:
                    return parent
                return process
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

    def update_games_processes(self, games: Iterable[InstalledGame]) -> Set[str]:
        """Matches currently running processes with the game executables and assigns those processes to games
        :returns     list of currently running games blizzard ids
        """
        running_games = set()
        for proc in psutil.process_iter():
            try:
                executable_path = proc.exe()
                process_name = proc.name()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
            for game in games:
                if executable_path in game.execs:
                    game.add_process(proc)
                    running_games.add(game.info.uid)
                if isinstance(game.info, ClassicGame):
                    executable = game.info.exe
                    if executable and executable in process_name:
                        game.add_process(proc)
                        running_games.add(game.info.uid)

        return running_games
