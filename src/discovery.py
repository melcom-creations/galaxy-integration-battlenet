"""Discover installed games from Battle.net's own aggregate and product database.

This is a local installation fallback, not a store catalog or proof of purchase.
Known definitions always take precedence. No launch identifiers are guessed.
"""

import json
import logging as log
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

from definitions import Blizzard, BlizzardGame


_CODE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,63}")
_NON_GAMES = {"agent", "agent_beta", "bna", "battle_net", "battle.net"}
MAX_AGGREGATE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class DiscoveredGame(BlizzardGame):
    launch_uri: str


@dataclass(frozen=True)
class AggregateGame:
    product_id: str
    name: str
    launch_uri: str
    last_played: str | None


def valid_code(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and _CODE.fullmatch(value) is not None


def valid_launch_uri(uri: object, product_id: object) -> TypeGuard[str]:
    return isinstance(uri, str) and valid_code(product_id) and uri == f"battlenet://game/{product_id}"


def parse_aggregate(data):
    """Accept only explicit game links; conflicting duplicate IDs are ambiguous."""
    if not isinstance(data, dict) or not isinstance(data.get("installed"), list):
        return {}
    if len(data["installed"]) > 2048:
        return {}
    games = {}
    ambiguous = set()
    for item in data["installed"]:
        if not isinstance(item, dict):
            continue
        code = item.get("product_id")
        name = item.get("name")
        uri = item.get("launch_uri")
        if not valid_code(code) or code.lower() in _NON_GAMES:
            continue
        if not isinstance(name, str) or not name.strip() or len(name) > 256:
            continue
        if any(ord(char) < 32 for char in name) or not valid_launch_uri(uri, code):
            continue
        timestamp = item.get("last_played_timestamp")
        last_played = None
        if type(timestamp) is int and 0 < timestamp < 100_000_000_000_000:
            last_played = str(timestamp // 1000)
        game = AggregateGame(code, name.strip(), uri, last_played)
        if code in games and games[code] != game:
            ambiguous.add(code)
        games[code] = game
    return {code: game for code, game in games.items() if code not in ambiguous}


def load_aggregate(path):
    try:
        with open(path, "rb") as stream:
            raw = stream.read(MAX_AGGREGATE_BYTES + 1)
        if len(raw) > MAX_AGGREGATE_BYTES:
            log.warning("Battle.net aggregate is too large; skipping automatic discovery")
            return {}
        return parse_aggregate(json.loads(raw))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError, RecursionError) as error:
        log.warning("Battle.net aggregate unavailable (%s); using known games", type(error).__name__)
        return {}


def discover_game(db_game, config_games, aggregate_games, database_games):
    """Return metadata only for an unambiguous, currently installed unknown game."""
    if not (db_game.installed or db_game.playable):
        return None
    if not valid_code(db_game.uninstall_tag) or not valid_code(db_game.ngdp):
        return None
    if db_game.uninstall_tag.lower() in _NON_GAMES or db_game.ngdp.lower() in _NON_GAMES:
        return None
    if sum(game.uninstall_tag == db_game.uninstall_tag for game in database_games) != 1:
        return None
    configs = [game for game in config_games if game.uninstall_tag == db_game.uninstall_tag]
    # Do not duplicate existing IDs or override special cases such as w2 -> w2be.
    for code in [db_game.uninstall_tag, db_game.ngdp, *(game.uid for game in configs)]:
        try:
            Blizzard[code]
            return None
        except KeyError:
            pass
    metadata = aggregate_games.get(db_game.ngdp)
    if metadata is None:
        return None
    path = Path(db_game.install_path)
    if not path.is_absolute() or path == Path(path.anchor) or not path.is_dir():
        return None
    # Shared WoW-style containers need explicit variant handling. Scanning the
    # whole container would attribute another installed variant's process here.
    for other in database_games:
        if other is db_game or not (other.installed or other.playable):
            continue
        other_path = Path(other.install_path)
        if path == other_path or path in other_path.parents or other_path in path.parents:
            log.warning("Automatic discovery deferred for %s: shared installation directory", db_game.uninstall_tag)
            return None
    last_played = configs[0].last_played if len(configs) == 1 else None
    info = DiscoveredGame(db_game.uninstall_tag, metadata.name, "", metadata.launch_uri)
    return info, last_played or metadata.last_played
