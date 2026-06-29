# Changelog

## Version 2.1.2-64bit

### Overview
Maintenance release. Rebuilt all third-party dependencies as clean 64-bit wheels for Python 3.13 via `melcom's Galaxy Plugin Scout v1.1.14`. Removed all development and build tools that were incorrectly bundled in `/modules/`.

### Changed
- **Dependency rebuild:** All third-party packages in `/modules/` were removed and reinstalled as verified 64-bit (`cp313-win_amd64`) wheels. All packages now carry proper `.dist-info` metadata.
- **`galaxy_plugin_api` now pip-managed:** The GOG Galaxy Plugin API (`galaxy/`) is now installed and updated via `pip install galaxy_plugin_api`.
- **Removed development tools:** `pytest`, `_pytest`, `py`, `pluggy`, `iniconfig`, `atomicwrites`, `pip`, `setuptools`, `wheel`, `piptools`, `pep517`, `click`, `colorama`, `invoke`, `pyparsing`, `_distutils_hack`, `importlib_metadata`, `zipp`, `tomli`, `asynctest`, `mypy_extensions` were identified as unused development and build tools and removed.

### Packages rebuilt (64-bit)
`aiohappyeyeballs`, `aiohttp`, `aiosignal`, `async_timeout`, `attrs`, `certifi`, `frozenlist`, `galaxy_plugin_api`, `idna`, `multidict`, `packaging`, `propcache`, `typing_extensions`, `yarl`

---

## Version 2.1.1-64bit

### Overview
This release reorganizes the plugin's file structure by moving third-party utility libraries and dependencies into a dedicated subfolder, keeping the root directory clean.

### Changed
- **Directory reorganization:** Relocated utility libraries (such as `typing_extensions`, `zipp`, `mypy_extensions`, etc.) from the root directory into a new `/Modules/` subdirectory.
- **Path configuration:** Updated the entry point (`itch.py`) to automatically add `/Modules/` to the system path (`sys.path`) during startup, ensuring all dependencies are resolved and loaded correctly.

---

## Version 2.1.0-64bit

### Overview
This release introduces native GOG Galaxy play-status tracking and game time (playtime) visualization, fixes the silent crash when launching games on native 64-bit runtimes, and significantly improves the robustness of the authentication and setup experience.

### Added
- **Playtime Syncing & Visualization (`get_game_time`):** Implemented GOG's `get_game_time` API hook in `itch.py`. Played minutes and the "last played" timestamp are now correctly loaded from GOG's persistent cache and displayed directly in the GOG Galaxy library interface.
- **Interactive Setup Copy Utility:** Added fallback-ready, clipboard-copying functionality directly to both `setup.html` and `setupDE.html`. Links and setup addresses can now be copied with a single click, completely bypassing the link-blocking restrictions of GOG Galaxy's embedded Chromium browser (CEF).

### Changed
- **Active Game Status Tracking:** The plugin now dynamically reports `LocalGameState.Running` to GOG Galaxy when a game is launched. The "Play" button now correctly changes to "Running" (greying out) and seamlessly reverts to "Installed" once the game process terminates.
- **Modernized Launch Logic (64-bit Fix):** Completely rewrote the process-launch mechanism in `localClientDbReader.py`. Replaced the outdated 32-bit `%windir%\Sysnative` directory reference and the `cmd.exe /c` redirection chain with a native `asyncio.create_subprocess_shell` execution leveraging the `cwd` working directory property. This fixes the silent failure of the "Play" button on modern 64-bit clients.
- **BOM-Resilient JSON Parser:** Upgraded the file-reading encoding for `credentials.json` to `utf-8-sig` in `itch.py`. This prevents silent parsing crashes caused by hidden byte-order marks (BOM) that are automatically inserted when users save credentials using default Windows text editors (Notepad).

### Removed
- **Legacy WOW64 Redirections:** Removed references to 32-bit Sysnative structures that are unavailable and unsupported under native 64-bit environments.

---

## Version 2.0.2-64bit

### Overview
This release modernizes the initial setup experience for the Itch.io integration and aligns the plugin with the current 64-bit GOG Galaxy client workflow. The setup process is now fully integrated into GOG Galaxy and no longer relies on outdated instructions or external configuration steps that are no longer required.

### Added
- **Integrated Setup Page (`setup.html`):** The plugin now displays a native GOG Galaxy setup page when no valid API token has been configured. Users are guided through the required preparation steps directly inside GOG Galaxy.
- **German Setup Page (`setupDE.html`):** Added a dedicated German-language version of the setup guide for German-speaking users.
- **Automatic Setup Detection:** The setup page continues to appear when the user clicks **Connect** until a valid API token has been configured.

### Changed
- **Setup Workflow Modernization:** The plugin now uses the bundled `credentials.json` workflow instead of older instructions that required users to create configuration files manually.
- **Documentation Updated:** The setup instructions were rewritten to reflect the actual behavior of the current plugin.
- **Native GOG Galaxy Experience:** Users remain inside GOG Galaxy during setup instead of being redirected through outdated configuration paths.
- **English and German Setup Guides Aligned:** Both setup pages now describe the same workflow and are consistent with the current plugin behavior.

### Removed
- **Outdated URL Entry Instructions:** Removed instructions referring to URL entry workflows that are not available in current GOG Galaxy versions.
- **Manual `credentials.json` Creation Instructions:** Removed documentation that instructed users to create `credentials.json` themselves. The file is now bundled with the plugin.
- **Legacy Setup Steps:** Removed setup guidance that no longer matches the actual authentication process.

### Technical Breakdown

#### 1. Integrated Setup Workflow
**Files:** `itch.py`, `setup.html`, `setupDE.html`

The plugin now checks whether a valid API token has been configured before attempting a connection. If the token is missing or invalid, the setup page is displayed directly inside GOG Galaxy. Once a valid token has been been entered, the integration connects immediately without displaying the setup page again.

#### 2. Documentation Cleanup
**Files:** `setup.html`, `setupDE.html`

Both setup pages were updated to reflect the actual plugin workflow. Instructions that referenced obsolete GOG Galaxy behavior, manual configuration file creation, or URL-based setup processes were removed.

#### 3. Credentials-Based Authentication
**Files:** `credentials.json`, `itch.py`

Authentication now centers around the bundled `credentials.json` file. Users only need to enter their personal Itch.io API token in the existing configuration file and save their changes.

---

## Version 2.0.1-64bit

### Overview
This release marks the first functional port of the original 32-bit itch.io GOG Galaxy plugin to the native 64-bit GOG Galaxy 2.1+ client. The primary goal was to replace all 32-bit Python extension modules with their 64-bit equivalents, resolve critical code bugs that prevented the plugin from running at all, and establish a working authentication flow against the itch.io OAuth API.

### Added
- **64-bit Library Migration:** All Python extension modules (`.pyd` files) were replaced with native 64-bit builds compiled for `cp313-win_amd64`. Affected packages include `aiohttp`, `frozenlist`, `multidict`, `yarl`, `charset_normalizer`, `_cffi_backend`, and others.
- **Missing Dependency Resolution:** Identified and added `propcache` and `aiohappyeyeballs` as required dependencies of `aiohttp` 3.14.x, which were not present in the original plugin package.
- **Token-Based Authentication (`credentials.json`):** Introduced a `credentials.json` file as the primary authentication mechanism. The plugin reads the itch.io OAuth access token directly from this file on startup, bypassing the GOG Galaxy embedded browser login flow entirely. This was necessary because Cloudflare's bot protection blocks authentication attempts from GOG Galaxy's embedded Chromium (CEF) browser.
- **Bearer Token HTTP Client:** Rewrote `http_client.py` to authenticate all API requests using an `Authorization: Bearer` header instead of the previous cookie-based approach, aligning with the itch.io API specification.
- **Plugin Callback Injection:** Introduced `set_plugin_callbacks()` in `localClientDbReader` to allow the plugin to inject `persistent_cache`, `update_game_time`, and `push_cache` references after initialization, resolving a structural dependency issue.
- **Galaxy SDK Upgrade:** Replaced the bundled `galaxy/` SDK folder with the current 64-bit SDK sourced from GOG's official 64-bit Steam plugin, ensuring full compatibility with the GOG Galaxy 2.1+ IPC protocol.
- **Initial Setup Guide (`setup.html`):** Created a standalone HTML setup guide explaining the full one-time setup process: installing the itch.io desktop client, logging in, generating an OAuth token via browser, and placing it in `credentials.json`.

### Fixed
- **`launch_game` Crash:** `localClientDbReader.launch_game()` referenced `self.persistent_cache`, `self.update_game_time`, and `self.push_cache` directly, which do not exist on that class — they belong to the `Plugin` object. Fixed by injecting these as callbacks from `itch.py` after initialization.
- **`get_local_games` Never Executed:** `get_local_games()` called `self.myLocalClientDbReader.get_local_games()` without `await`, causing the coroutine to be silently discarded and local games to never be reported.
- **Missing Cave Guard:** `launch_game()` did not handle the case where no matching cave (installed game record) was found in the butler database, resulting in an unhandled `IndexError`. Added an explicit check with a logged warning.
- **`sqlite3.OperationalError` on Missing Database:** The butler database does not exist until the itch.io desktop client has been installed and logged into at least once. Added clear error handling and documented this as a prerequisite in the setup guide.

### Changed
- **`http_client.py` Refactored:** Removed the legacy cookie-passing mechanism. Authentication is now handled exclusively via Bearer token sourced from `credentials.json`.
- **`itch.py` `authenticate()` Flow:** Modified to check for a locally stored `credentials.json` before falling back to the web-based OAuth login flow, preventing the Cloudflare loop entirely for users who have completed setup.

### Removed
- **32-bit `.pyd` Extension Modules:** All 32-bit compiled Python extensions were removed and replaced with their 64-bit equivalents.
- **Cookie-Based Auth Remnants:** Removed leftover cookie-handling logic in `http_client.py` that was incompatible with the itch.io Bearer token API.

---

## Version Prototype / v0.0.6 and Earlier
*(Legacy releases by [tauqua](https://github.com/tauqua) - see the [original repository](https://github.com/tauqua/gog-galaxy-itch.io/releases/tag/v0.0.6) for historical changelog entries.)*