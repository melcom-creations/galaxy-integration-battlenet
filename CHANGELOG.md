# Changelog

All notable changes to this plugin will be documented in this file.

---

## Version 2.1.8-64bit

- Fixed startup path detection for bundled dependencies.
- plugin.py now detects both 'modules' and 'Modules', preventing ModuleNotFoundError on case-sensitive systems.
- **Improved sys.path handling:** Replaced complex fallback logic with direct, robust path resolution using `os.path.abspath()`. This ensures bundled modules are correctly loaded even with edge-case path configurations.

## Version 2.1.7-64bit

### Overview
This maintenance and optimization release performs a comprehensive cleanup and modernization of the plugin's dependency directory (`/modules/`). It removes obsolete legacy packages, cleanly updates all third-party libraries to their latest stable 2026 versions using the `GalaxyPluginScout` tool, and installs official metadata (`.dist-info`) records for robust runtime execution.

### Changed
- **Full Dependency Modernization:** Successfully updated the entire third-party library suite to their latest stable releases using pip-targeted wheel resolution (Python 3.13, 64-bit):
  - `aiohttp` updated to **v3.14.1**
  - `yarl` updated to **v1.24.2**
  - `multidict` updated to **v6.7.1**
  - `propcache` updated to **v0.5.2**
  - `requests` updated to **v2.34.2**
  - `urllib3` updated to **v2.7.0**
  - `idna` updated to **v3.18**
  - `chardet` updated to **v7.4.3**
  - `charset_normalizer` updated to **v3.4.7**
  - `aiosignal` updated to **v1.4.0**
  - `frozenlist` updated to **v1.8.0**
  - `aiohappyeyeballs` updated to **v2.6.2**
  - `certifi` updated to **v2026.6.17**
  - `psutil` updated to **v7.2.2**
- **Standardized API Mappings:** Re-aligned core GOG Galaxy and serialization schemas by mapping the local `galaxy` folder to the official PyPI `galaxy_plugin_api` (**v0.71**) distribution, and the `google` namespace to the modern `protobuf` (**v7.35.1**) library.
- **Metadata Integration:** All updated packages now include their official `.dist-info` metadata directories in `/modules/`, ensuring reliable package tracking and standard-compliant Python imports.

### Fixed
- **Obsolete Dependency Pruning (Zero-Leak Cleanup):** Cleanly pruned several deprecated, redundant, or unused legacy libraries from `/modules/` to reduce clutter and filesystem footprint:
  - Removed `cffi` (no longer required by modern active dependencies).
  - Removed the redundant `examples/` folder.
  - Removed `six.py` (obsolete Python 2 compatibility layer).
- **Consolidated Attribute Namespace:** Unified the redundant update pipeline for the `attr` and `attrs` directories, ensuring only verified modern `attrs` (**v26.1.0**) packages are processed.

---

## Version 2.1.6-64bit

### Overview
This release introduces a robust, local playtime tracking system with commercial rounding ("kaufmännisch-round") for all Battle.net games. It also implements an advanced hybrid fallback in GOG Galaxy, allowing GOG to display locally accumulated playtime for standard games while preserving the official Overwatch web API statistics.

### Added
- **Local Playtime Tracking:** Enabled background monitoring of running game processes. The plugin now records session start and end timestamps directly inside the existing `_notify_about_game_stop` execution path, updating last played dates and total minutes dynamically.
- **Kaufmännisch-Round Playtime:** Playtime session tracking now commercially rounds (`round()`) to the nearest minute, preventing strict truncation loss and ensuring even brief playing sessions are credited.

### Changed
- **Hybrid Playtime Fallback:** Upgraded the `get_game_time()` routine. GOG Galaxy now automatically reads and displays locally tracked, rounded playing times from the persistent cache, falling back to the official Blizzard web API statistics for *Overwatch* as needed.

---

## Version 2.1.5-64bit

### Overview
This release reorganizes the plugin's file structure by moving third-party libraries and compiled dependencies into a dedicated subfolder, keeping the root directory clean.

### Changed
- **Directory reorganization:** Moved all utility libraries and third-party dependencies from the root directory into a new `/Modules/` subdirectory.
- **Path configuration:** Updated the entry points (`__init__.py` and `plugin.py`) to automatically add `/Modules/` to the system path (`sys.path`) during startup, ensuring all dependencies are loaded correctly.
- **Code comments cleanup:** Internal code comments were verified and kept strictly in US-English to maintain consistency.

---

## Version 2.1.4-64bit

### Overview
This release improves the first-time setup experience by replacing the previous external setup-page browser launch with a native GOG Galaxy setup dialog. New users can now complete the initial Battle.net plugin configuration without being redirected to their default web browser.

### Changed
- **Native GOG Galaxy setup experience:** The setup workflow now uses the GOG Galaxy `web_session` mechanism to display `setup.html` directly inside the client instead of opening the page through the operating system's default browser.
- **Improved onboarding flow:** Users remain inside the GOG Galaxy interface while reviewing the setup instructions and configuring their Battle.net OAuth credentials.

### Technical Notes
- The setup page is now delivered through the same internal GOG Galaxy dialog mechanism already used by other supported setup workflows.
- Existing authentication behavior, OAuth processing, credential storage, and account linking logic remain unchanged.

### Known Limitation
- **Warcraft III: Reign of Chaos and Warcraft III: The Frozen Throne setup guidance:** The bundled `wc3_classic_info.html` page still opens through the system browser. A review of the current plugin architecture showed that the page is triggered from the installation notification workflow, while the native GOG HTML dialog mechanism is only exposed through the authentication flow via `NextStep("web_session", ...)`. A direct migration to the native dialog path could not be implemented using the documented and verifiable APIs available in the current codebase without introducing unsupported behavior.

---

## Version 2.1.3-64bit

### Overview
This release resolves a long-standing false-positive installation state for the Warcraft III classic titles (*Reign of Chaos* and *The Frozen Throne*). Both games were incorrectly detected as installed due to a shared Windows Registry key with Warcraft III: Reforged, making them appear playable in GOG Galaxy while actually being unlaunchable. The fix disables registry-based detection for these two titles entirely and replaces the broken install flow with a local guided setup page that explains both available play routes.

### Fixed
- **False "Installed" state for Warcraft® III: Reign of Chaos® and Warcraft® III: The Frozen Throne®:** Both classic titles shared the registry path `Warcraft III` under `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall` with Warcraft III: Reforged. The plugin's `_add_classic_game()` routine in `local_games.py` resolved this key to the Reforged install path and marked both classics as installed and playable — even though their standalone executables were not present. Clicking Play would silently launch Reforged instead. Fixed by setting `registry_path=None` for `w3ROC` and `w3tft` in `definitions.py`, permanently disabling false-positive registry detection for these entries.

- **Unlaunchable classic WC3 titles silently starting Reforged:** Because `install_path` resolved to the Reforged directory, `launch_game()` in `plugin.py` called `subprocess.Popen()` on `Warcraft III.exe` inside that path — which is the Reforged executable. The user clicked a classic game and Reforged launched instead, with no error or indication of what happened.

### Added
- **`wc3_classic_info.html` – Local Classic Games Setup Guide:** A self-contained HTML guide (matching the visual style of `setup.html`) that opens from the plugin when the user clicks **Install** for either classic WC3 title in GOG Galaxy. The page covers:
  - The prerequisite of owning and having registered a valid product key
  - **Route A (Standalone):** Downloading the classic executables directly from the Blizzard account page under *Account Settings → Games & Subscriptions → Classic Games*
  - **Route B (Battle.net Launcher):** Selecting *Warcraft III – Legacy TFT 1.29* from the version dropdown inside the Reforged launcher (requires Warcraft III: Reforged to be installed)

### Changed
- **`definitions.py` – `w3ROC` and `w3tft` registry detection disabled:** Both `ClassicGame` entries now omit `registry_path`, `registry_installation_key`, `exe`, and `bundle_id`. This prevents `_add_classic_game()` from ever matching them against the shared Reforged registry key.
- **`plugin.py` – `install_game()` redirects WC3 classics to local info page:** Rather than opening a generic Blizzard download URL (which pointed to the Battle.net launcher rather than the classic download page), `install_game()` now opens `wc3_classic_info.html` for `w3ROC` and `w3tft`, giving the user actionable guidance specific to these titles.

### Technical Breakdown

#### 1. Root Cause: Shared Registry Key
**Files:** `definitions.py`, `local_games.py`

**Problem:** Blizzard's modern installer for Warcraft III: Reforged registers itself under `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Warcraft III` — the same key that was historically used by the classic standalone installers. The plugin's `_add_classic_game()` function opened this key using `winreg.KEY_WOW64_32KEY` (correctly added in 2.1.0 for 32-bit game detection), found a valid `InstallLocation` value pointing to the Reforged directory, and returned a fully populated `InstalledGame` object for both `w3ROC` and `w3tft`. Both entries were marked `playable=True` and `installed=True`.

**Solution:** Set `registry_path=None` for both entries in `definitions.py`. The `_add_classic_game()` guard `if game.registry_path:` causes the function to return `None` immediately, so neither title is ever added to `installed_classic_games`. GOG Galaxy correctly shows them as not installed.

#### 2. Broken Launch Path
**Files:** `plugin.py`

**Problem:** `launch_game()` checked `isinstance(game.info, ClassicGame)` and, finding a match, called `subprocess.Popen(os.path.join(game.install_path, game.info.exe))`. Since `install_path` was the Reforged directory and `exe` was `Warcraft III.exe`, this silently launched Reforged. No error was raised, no feedback was given to the user.

**Solution:** With the registry fix in place, `get_installed_games()` no longer returns entries for `w3ROC` or `w3tft`, so `launch_game()` falls through to `install_game()` instead — which now opens the info page.

#### 3. Guided Setup Page
**Files:** `wc3_classic_info.html`, `plugin.py`

The two classic WC3 titles occupy a unique position: they are real purchased games with no automatic install path the plugin can use. Rather than silently redirecting to a generic URL or doing nothing, `install_game()` now opens a locally bundled HTML page that gives the user the full picture and the correct next steps for their specific situation.

---


## Version 2.1.2-64bit

### Overview
This maintenance and stability release focuses on improving runtime robustness inside the Battle.net integration. The update hardens background services, reduces the risk of synchronization inconsistencies, improves thread-safety, removes event-loop blocking behavior, and protects the plugin against temporary backend and filesystem failures.

### Fixed
- **Blocking background synchronization paths:** Removed plugin-adjacent blocking wait behavior that could stall Galaxy-facing execution paths for several seconds.
- **Race condition in running game tracking:** Shared game-monitoring state is now protected against concurrent access from multiple background update sources.
- **Unsafe concurrent data access:** Critical shared structures were hardened to avoid state corruption during simultaneous watcher and updater activity.
- **Background task termination risk:** Unexpected exceptions no longer permanently stop critical watcher or updater tasks.
- **Watcher reliability issues:** Filesystem monitoring paths now recover more gracefully from transient failures.
- **Potential false library modifications during temporary failures:** Synchronization logic is more conservative when backend data sources are temporarily unavailable.

### Changed
- **Thread synchronization improved:** Internal watcher and updater coordination now uses safer access patterns for shared runtime state.
- **Background services hardened:** Long-running tasks now tolerate unexpected runtime failures more gracefully.
- **Library synchronization behavior improved:** Existing user data is preserved whenever source validity cannot be established with certainty.
- **Event-loop compatibility improved:** Internal execution paths were reviewed to minimize unnecessary blocking behavior.

### Technical Breakdown

#### 1. Removal of blocking wait paths
**Files:** `local_client_base.py`, `local_games.py`

Several execution paths previously relied on blocking waits during background operations. These paths were reworked to avoid unnecessary stalls and reduce the likelihood of delayed Galaxy event processing.

#### 2. Thread-safe running game monitoring
**Files:** `plugin.py`

Access to shared running-game tracking structures is now synchronized, preventing race conditions when multiple background systems report game state changes simultaneously.

#### 3. Background task resilience
**Files:** `watcher.py`, `local_client_base.py`

Critical watcher and updater loops now handle unexpected exceptions more defensively, reducing the risk of silently terminated monitoring services.

#### 4. Synchronization safety improvements
**Files:** `plugin.py`

Library synchronization paths now avoid unnecessary destructive updates during temporary backend failures and prioritize preservation of previously known valid data.

## Version 2.1.1-64bit

### Overview
This release adds a guided one-time setup flow for new users who install the plugin without pre-configured OAuth credentials. A setup page now opens automatically in the browser, and the plugin handles missing credentials gracefully without crashing or showing confusing error dialogs.

### Added
- **Integrated Setup Page (`setup.html`):** When the plugin detects empty `CLIENT_ID` or `CLIENT_SECRET` values in `consts.py`, it returns a GOG Galaxy `web_session` setup step that loads `setup.html` inside the client. The page provides a step-by-step guide for registering a personal Blizzard OAuth client and entering the credentials, including an explicit reminder to restart GOG Galaxy after saving `consts.py`.

- **Graceful Handling of Missing Credentials:** `authenticate()` now detects empty credentials before attempting any network calls. Instead of triggering a `401 Bad client credentials` dialog or spinning indefinitely on "Wird verknüpft...", the plugin waits 3 seconds and raises `InvalidCredentials`, returning the Connect button to its default state so the user can act on the setup instructions.

### Fixed
- **`ImportError: cannot import name 'Platform'` on startup:** The platform detection block in `consts.py` lacked an `else` branch for Linux and unrecognized platforms. If `sys.platform` was neither `win32` nor `darwin`, `SYSTEM` remained undefined, causing a `NameError` that aborted the module import before `Platform` could be exported. Added `else: SYSTEM = Platform.LINUX` to resolve this.


## Version 2.1.0-64bit

### Overview
This release resolves the complete OAuth authentication chain for the 64-bit GOG Galaxy client using a custom Blizzard developer OAuth client. The original shared community OAuth credentials had been revoked by Blizzard, making login impossible. Additionally, the `protobuf` library was upgraded and regenerated for full Python 3.13 compatibility, game database coverage was expanded with Diablo IV support, and a login performance improvement was added.

### Added
- **Custom OAuth Client Support:** The plugin now requires users to register their own free OAuth client at [develop.battle.net](https://develop.battle.net). The original shared `CLIENT_ID` and `CLIENT_SECRET` were revoked by Blizzard. A personal OAuth client restores full login functionality permanently.
  - `CLIENT_ID` and `CLIENT_SECRET` are now configured in `consts.py`
  - `state` parameter added to the OAuth authorization URL (required by Blizzard's updated API)

- **Diablo IV (`fenris`) Support:** Added `fenris` as a proper game entry in `definitions.py`. The Battle.net internal `uninstall_tag` for Diablo IV is `fenris`, not `diablo4`. This caused Diablo IV to be silently skipped with "not known blizzard game" in previous versions.

- **Login Window Pre-warming:** Region detection (`guess_region()`) is now executed in the background during plugin startup (`__delayed_handshake()`). This eliminates the 3–4 second delay users previously experienced before the Battle.net login window appeared after clicking "Connect".

### Fixed
- **protobuf `TypeError` on startup (Critical):** The bundled `product_db_pb2.py` was generated with an outdated `protoc` compiler and was incompatible with `protobuf >= 4.x`. Regenerated using `grpc_tools.protoc` (Protobuf Python Version 6.33.5). Removed the stale `protobuf-3.7.1-py3.7-nspkg.pth` path file that overrode the updated `google` package.

- **OAuth `400` error – missing `state` parameter:** Blizzard's OAuth authorization endpoint now requires a `state` parameter for CSRF protection. Added `secrets.token_hex(16)` state generation in `http_client.py → authenticate_using_login()`.

- **Silent cookie refresh loop causing disconnect:** After a successful login, the plugin incorrectly triggered `refresh_access_token_with_cookies()` immediately. This method attempts to silently re-authenticate using stored cookies via Blizzard's `account-settings` endpoint — a flow that is not supported with a custom OAuth client, causing an infinite 401 loop and plugin disconnect. Removed the `refresh_cookies()` call from `pass_login_credentials()`.

- **`authentication_lost` fired twice causing GOG Galaxy EOF disconnect:** When `games-and-subs` returned 401, `_authenticated_request()` in `backend.py` called `lost_authentication()` before the fallback in `plugin.py` could handle it gracefully. This sent two `authentication_lost` notifications to GOG Galaxy, which responded with EOF. Fixed by removing `lost_authentication()` from `_authenticated_request()` — error handling is now solely the caller's responsibility.

- **Owned games import failure (`games-and-subs` 401):** Blizzard's `/api/games-and-subs` and `/api/classic-games` endpoints are internal and not accessible to external OAuth clients regardless of scope. `get_owned_games()` in `plugin.py` now catches `AuthenticationRequired` from these endpoints and falls back to the locally installed games from the Battle.net database, returning them as `SinglePurchase`.

- **Duplicate Diablo IV entries:** Both `fenris` (installed, `SinglePurchase`) and `diablo4` (F2P fallback) appeared simultaneously in the library. Fixed by consolidating all `diablo4`/`fenris` mappings in `TITLE_ID_MAP` to point exclusively to `fenris`, and removing the redundant `BlizzardGame('diablo4', ...)` entry.

### Changed
- **`backend.py` – Simplified `_authenticated_request()`:** Removed the automatic `refresh_cookies()` + `lost_authentication()` retry loop. The method now raises authentication errors directly to the caller.
- **`backend.py` – `refresh_cookies()` is now a no-op:** Silent cookie-based token refresh is not supported with a custom OAuth client. The method logs a debug message and returns immediately.
- **`definitions.py` – `fenris` is now the canonical Diablo IV entry:** All `TITLE_ID_MAP` references to `diablo4` now resolve to `fenris`. The legacy `BlizzardGame('diablo4', ...)` entry has been removed.

### Known Limitations
> ⚠️ **Game library shows unowned Free-to-Play titles**
>
> Blizzard's `/api/games-and-subs` endpoint is restricted to internal first-party OAuth clients and returns HTTP 401 for any externally registered application, regardless of requested scopes. Because of this, the plugin cannot determine which games you have actually purchased versus which are merely free-to-play. As a result, all F2P titles defined in the plugin (StarCraft, StarCraft II, World of Warcraft, Hearthstone, Heroes of the Storm, Diablo Immortal, Warcraft Rumble, Call of Duty: Modern Warfare / II / III, Black Ops 6, etc.) will always appear in your GOG Galaxy library, even if you have never played or owned them.
>
> **Workaround:** Right-click any unwanted game in GOG Galaxy → **Hide**. The game will no longer appear in your library view.

---

## Version 2.0.0-64bit

### Overview
A comprehensive modernization of the Battle.net integration for the 64-bit GOG Galaxy client. This release permanently resolves the persistent session drop bug, restores classic game detection, bundles native 64-bit dependencies, and significantly expands game database coverage for modern Blizzard and Activision titles.

### Added
- **Modern Game Database Expansion:** Completely updated the internal game definitions to support modern Blizzard and Activision releases. The plugin now successfully recognizes, tracks, and launches:
  - Diablo IV
  - Diablo Immortal
  - Warcraft I: Remastered & Warcraft II: Remastered
  - Warcraft: Orcs & Humans (Classic) & Warcraft II: Battle.net Edition
  - Warcraft Rumble
  - Call of Duty: Modern Warfare II, Modern Warfare III, Black Ops 6, and Vanguard
  - Crash Bandicoot 4: It's About Time

- **Native 64-bit Architecture:** Bundled pre-compiled native 64-bit Python 3.13 C-extensions (`aiohttp`, `yarl`, `psutil`, `cffi`, `multidict`, `frozenlist`) to prevent `ImportError` (DLL load failed) crashes under the new GOG Galaxy client.

- **Modern Dependencies:** Added new mandatory network dependencies (`propcache` and `aiohappyeyeballs`) required by the modernized `aiohttp` and `yarl` libraries.

### Fixed
- **Session Drop Bug (Critical):** Engineered a silent OAuth interceptor mechanism to permanently resolve the notorious "random logout after restart" issue. When the short-lived Blizzard `access_token` expires, the plugin now seamlessly navigates the backend redirect chain using stored cookies, intercepts the new authorization code, and automatically exchanges it for a fresh access token in the background. Users remain logged in indefinitely.

- **Classic Games Detection (64-bit Registry Fix):** Added the `winreg.KEY_WOW64_32KEY` flag to Windows Registry queries in `local_games.py`. The 64-bit Python interpreter now correctly reads from the 32-bit `Wow6432Node` hive, ensuring classic 32-bit Blizzard games (like *Diablo II* and *StarCraft*) are successfully detected as "Installed".

- **Thread Lifecycle Crash:** Replaced the deprecated `isAlive()` method with the modern `is_alive()` in `local_games.py`. This prevents fatal `AttributeError` exceptions during background local game scans under Python 3.13.

- **Plugin Initialization Crash:** Removed the deprecated and deleted `distutils.version` module import from `plugin.py`, fixing immediate `ModuleNotFoundError` crashes upon plugin boot.

### Changed
- **Update Protection:** Removed `update_url` from `manifest.json` to prevent GOG Galaxy from automatically overwriting this functional 64-bit fix with the legacy 32-bit version from the original repository.

- **Asyncio Modernization:** Updated `asyncio.get_event_loop()` calls to `asyncio.get_running_loop()` where applicable to comply with Python 3.13 standards.

### Technical Breakdown

#### 1. Session Management: The Permanent Login Fix
**Files:** `http_client.py`, `backend.py`

**Problem:** The original plugin suffered from a critical bug where users were randomly logged out after restarting GOG Galaxy. This occurred because Blizzard's `access_token` has a very short lifespan. While the legacy implementation attempted session refresh using stored cookies, it failed to properly extract the newly generated authorization code from the OAuth redirect chain, causing authentication to fail and forcing manual re-login.

**Solution:** Implemented `refresh_access_token_with_cookies()`, a sophisticated OAuth interceptor that:
- Detects when the short-lived `access_token` expires
- Navigates the Blizzard backend authorization chain using stored web cookies
- Silently intercepts the new authorization code from the redirect flow
- Automatically exchanges the code for a fresh access token in the background
- Maintains session persistence across client restarts

**Impact:** Users stay permanently logged in without manual intervention.

#### 2. Game Database: Modern Title Support
**Files:** `definitions.py`

**Problem:** GOG Galaxy relies on hardcoded product IDs (NGDP codes) to recognize and launch Battle.net games. The outdated plugin database completely ignored modern releases, meaning contemporary titles like *Diablo IV*, *Warcraft Remastered*, and recent *Call of Duty* franchises would not appear in GOG Galaxy even when installed.

**Solution:** Rebuilt the game definitions database from scratch with:
- Comprehensive ID mappings for all modern Blizzard and Activision titles
- String-based fallback matching for titles with multiple SKU variants
- Support for both regional and seasonal game releases
- Proper categorization for remastered vs. classic versions

**Impact:** All modern Blizzard and Activision games now integrate seamlessly with GOG Galaxy.

#### 3. 64-bit Architecture & Python 3.13 Compliance
**Files:** `local_games.py`, `plugin.py`

**Problem:** The transition from 32-bit to 64-bit Python 3.13 introduced three critical incompatibilities:
1. The `distutils` module was removed from Python 3.12+, causing immediate boot failures
2. The threading method `isAlive()` was removed in Python 3.10, crashing the local game scanner
3. The 64-bit interpreter queries the 64-bit Windows Registry by default, failing to locate 32-bit classic games stored in the `Wow6432Node` hive

**Solution:** Applied targeted modernization:
- Removed all deprecated `distutils` imports and replaced with standard library equivalents
- Migrated threading calls to use the modern `is_alive()` method
- Added the `winreg.KEY_WOW64_32KEY` flag to all registry queries, enabling the 64-bit interpreter to properly access and detect 32-bit classic game installations

**Impact:** Plugin boots successfully, background game scanning completes without crashes, and classic 32-bit titles are properly detected.

#### 4. Compiled Dependencies: 64-bit Binaries
**Files:** `modules/`

**Problem:** The original plugin shipped with 32-bit compiled C-extensions (`aiohttp`, `yarl`, `psutil`, `cffi`, `multidict`, `frozenlist`) that triggered fatal `ImportError` (DLL load failed) exceptions when loaded under the 64-bit GOG Galaxy client.

**Solution:** Replaced all legacy 32-bit dependencies with:
- Native 64-bit Python 3.13 compiled versions of all C-extensions
- Additional network dependencies (`propcache`, `aiohappyeyeballs`) required by modern `aiohttp` and `yarl` versions
- Proper dependency versioning to ensure compatibility with the Python 3.13 runtime

**Impact:** All network operations execute without DLL load failures, providing stable async communication with Battle.net services.

---

## Version 0.44 and Earlier
*(Legacy releases by [FriendsOfGalaxy](https://github.com/FriendsOfGalaxy) - see the [original repository](https://github.com/FriendsOfGalaxy/galaxy-integration-battlenet/releases) for historical changelog entries.)*