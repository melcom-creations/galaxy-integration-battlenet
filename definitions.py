import dataclasses as dc
import json
from requests.cookies import RequestsCookieJar
from typing import Any, Optional, Dict, List


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if dc.is_dataclass(o) and not isinstance(o, type):
            return dc.asdict(o)
        return super().default(o)


@dc.dataclass
class WebsiteAuthData(object):
    cookie_jar: RequestsCookieJar
    access_token: str
    region: str


@dc.dataclass(frozen=True)
class BlizzardGame:
    uid: str
    name: str
    family: str


@dc.dataclass(frozen=True)
class ClassicGame(BlizzardGame):
    registry_path: Optional[str] = None
    registry_installation_key: Optional[str] = None
    exe: Optional[str] = None
    bundle_id: Optional[str] = None


@dc.dataclass
class RegionalGameInfo:
    uid: str
    try_for_free: bool


@dc.dataclass
class ConfigGameInfo(object):
    uid: str
    uninstall_tag: Optional[str]
    last_played: Optional[str]


@dc.dataclass
class ProductDbInfo(object):
    uninstall_tag: str
    ngdp: str = ''
    install_path: str = ''
    version: str = ''
    playable: bool = False
    installed: bool = False


class Singleton(type):
    _instances = {}  # type: ignore

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class _Blizzard(object, metaclass=Singleton):
    TITLE_ID_MAP = {
        21297: RegionalGameInfo('s1', True),
        21298: RegionalGameInfo('s2', True),
        5730135: RegionalGameInfo('wow', True),
        5272175: RegionalGameInfo('prometheus', False),
        22323: RegionalGameInfo('w3', False),
        1146311730: RegionalGameInfo('destiny2', False),
        1465140039: RegionalGameInfo('hs_beta', True),
        1214607983: RegionalGameInfo('heroes', True),
        17459: RegionalGameInfo('diablo3', True),
        4613486: RegionalGameInfo('fenris', False),
        1447645266: RegionalGameInfo('viper', False),
        1329875278: RegionalGameInfo('odin', True),
        1279351378: RegionalGameInfo('lazarus', False),
        1514493267: RegionalGameInfo('zeus', False),
        1381257807: RegionalGameInfo('rtro', False),
        1464615513: RegionalGameInfo('wlby', False),
        5198665: RegionalGameInfo('osi', False),
        1179603525: RegionalGameInfo('fore', False),
        
        # Blizzard product TitleID and UID mappings.
        1095647827: RegionalGameInfo('anbs', True),    # Diablo Immortal (PC)
        5714258: RegionalGameInfo('w1r', True),       # Warcraft I: Remastered
        5714514: RegionalGameInfo('w2r', True),       # Warcraft II: Remastered
        
        # Fallback strings for modern Battle.net NGDP queries.
        'diablo4': RegionalGameInfo('fenris', False),
        'diablo_immortal': RegionalGameInfo('anbs', True),
        'anbs': RegionalGameInfo('anbs', True),
        'fenris': RegionalGameInfo('fenris', False),
        'w1': RegionalGameInfo('w1', True),
        'w1r': RegionalGameInfo('w1r', True),
        'w2be': RegionalGameInfo('w2be', True),
        'w2r': RegionalGameInfo('w2r', True),
        'gryphon': RegionalGameInfo('gryphon', True),
        'auks': RegionalGameInfo('auks', True),
        'coop': RegionalGameInfo('coop', True),
        'spot': RegionalGameInfo('spot', True),
        'wlby': RegionalGameInfo('wlby', False),
        'osi': RegionalGameInfo('osi', False),
    }
    TITLE_ID_MAP_CN = {
        **TITLE_ID_MAP,
        17459: RegionalGameInfo('d3cn', False)
    }
    BATTLENET_GAMES = [
        BlizzardGame('s1', 'StarCraft', 'S1'),
        BlizzardGame('s2', 'StarCraft II', 'S2'),
        BlizzardGame('wow', 'World of Warcraft', 'WoW'),
        BlizzardGame('wow_classic', 'World of Warcraft Classic', 'WoW_wow_classic'),
        BlizzardGame('prometheus', 'Overwatch', 'Pro'),
        BlizzardGame('w3', 'Warcraft III', 'W3'),
        BlizzardGame('hs_beta', 'Hearthstone', 'WTCG'),
        BlizzardGame('heroes', 'Heroes of the Storm', 'Hero'),
        BlizzardGame('d3cn', '暗黑破壞神III', 'D3CN'),
        BlizzardGame('diablo3', 'Diablo III', 'D3'),
        BlizzardGame('viper', 'Call of Duty: Black Ops 4', 'VIPR'),
        BlizzardGame('odin', 'Call of Duty: Modern Warfare', 'ODIN'),
        BlizzardGame('lazarus', 'Call of Duty: MW2 Campaign Remastered', 'LAZR'),
        BlizzardGame('zeus', 'Call of Duty: Black Ops Cold War', 'ZEUS'),
        BlizzardGame('rtro', 'Blizzard Arcade Collection', 'RTRO'),
        BlizzardGame('wlby', 'Crash Bandicoot 4: It\'s About Time', 'WLBY'),
        BlizzardGame('osi', 'Diablo® II: Resurrected', 'OSI'),
        BlizzardGame('fore', 'Call of Duty: Vanguard', 'FORE'),
        
        # Modern Battle.net game definitions used by the plugin.
        BlizzardGame('anbs', 'Diablo Immortal', 'ANBS'),
        BlizzardGame('w1', 'Warcraft: Orcs & Humans (Classic)', 'W1'),
        BlizzardGame('w1r', 'Warcraft I: Remastered', 'W1R'),
        BlizzardGame('w2be', 'Warcraft II: Tides of Darkness', 'W2'),
        BlizzardGame('w2r', 'Warcraft II: Remastered', 'W2R'),
        BlizzardGame('gryphon', 'Warcraft Rumble', 'GRY'),
        BlizzardGame('auks', 'Call of Duty: Modern Warfare II', 'AUKS'),
        BlizzardGame('coop', 'Call of Duty: Modern Warfare III', 'COOP'),
        BlizzardGame('spot', 'Call of Duty: Black Ops 6', 'SPOT'),
        BlizzardGame('fenris', 'Diablo IV', 'D4')
    ]
    CLASSIC_GAMES = [
        ClassicGame('d1', 'Diablo', 'Diablo', 'Diablo', 'InstallLocation', 'Diablo.exe', 'com.blizzard.diablo'),
        ClassicGame('d2', 'Diablo® II', 'Diablo II', 'Diablo II', 'DisplayIcon', "Game.exe", "com.blizzard.diabloii"),
        ClassicGame('d2LOD', 'Diablo® II: Lord of Destruction®', 'Diablo II'),
        # w3ROC and w3tft intentionally do not use registry_path.
        # Blizzard merges both classic Warcraft III releases into "Warcraft III - Legacy TFT 1.29" inside the
        # Reforged launcher.
        # The legacy "Warcraft III" registry key points to the Reforged install, so registry-based detection
        # would mark these entries as installed even when they are not.
        # Leaving registry_path unset avoids false positives and lets the plugin handle installation explicitly.
        ClassicGame('w3ROC', 'Warcraft® III: Reign of Chaos',  'Warcraft III'),
        ClassicGame('w3tft', 'Warcraft® III: The Frozen Throne®',  'Warcraft III'),
        ClassicGame('sca', 'StarCraft® Anthology', 'Starcraft', 'StarCraft')
    ]

    def __init__(self):
        self._games = {game.uid: game for game in self.BATTLENET_GAMES + self.CLASSIC_GAMES}
        # The local Battle.net agent registers the installed Warcraft II: Tides of Darkness
        # (Battle.net's classic re-release, formerly marketed as "Battle.net Edition") under
        # the config/uninstall-tag UID 'w2', while the public-facing game ID that GOG Galaxy's
        # own catalog actually matches with proper cover art / videos is 'w2be'.
        # Without this alias, Blizzard['w2'] raises a KeyError and the local scan discards the
        # game as "not known blizzard game" -> it never shows up as installed.
        self._games['w2'] = self._games['w2be']

    def __getitem__(self, key: str) -> BlizzardGame:
        return self._games[key]

    def game_by_title_id(self, title_id: int, cn: bool) -> BlizzardGame:
        if cn:
            regional_info = self.TITLE_ID_MAP_CN[title_id]
        else:
            regional_info = self.TITLE_ID_MAP[title_id]
        return self[regional_info.uid]

    def try_for_free_games(self, cn: bool) -> List[BlizzardGame]:
        return [
            self[info.uid] for info
            in (self.TITLE_ID_MAP_CN if cn else self.TITLE_ID_MAP).values()
            if info.try_for_free
        ]


Blizzard = _Blizzard()
