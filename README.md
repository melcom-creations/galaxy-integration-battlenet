# Battle.net Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This plugin imports your Battle.net library into GOG Galaxy 2.1+ 64-bit. Based on the original community integration, it has been updated for the current GOG Galaxy client and Python 3.13, with restored OAuth authentication and current game definitions.

The steps below are for Windows. Dependencies are bundled; no separate Python installation is needed.

[Installation](#-installation) | [First Start](#-first-start-and-initial-sync) | [Troubleshooting](#-troubleshooting) | [Support & Feedback](#-support--feedback)

## ✨ Features

* Imports purchased Battle.net games into GOG Galaxy
* Includes supported free-to-play Battle.net titles
* Detects locally installed Battle.net games
* Automatically discovers additional installed games on Windows when Battle.net provides matching installation metadata and a game launch link
* Launches, installs, and uninstalls games through the Battle.net desktop app
* Tracks local game time for Battle.net games
* Uses personal Blizzard developer credentials for OAuth authentication
* Accepts and saves personal OAuth credentials through a guided setup page inside GOG Galaxy
* Keeps OAuth configuration outside the plugin folder and protects it with Windows DPAPI
* Supports current game definitions, including Diablo IV
* Restores detection of classic 32-bit games on 64-bit Windows
* Handles Warcraft III classic titles without falsely marking them as installed

> [!NOTE]
> macOS compatibility may be technically possible, but it is currently untested because I do not have access to a Mac. If you use macOS and would like to help test the integration, feel free to contact me.

## 📦 Installation

### 🔄 Automatic Installation with Plugin Updater (Recommended)

Use the [melcom GOG Galaxy Plugin Updater](https://github.com/melcom-creations/galaxy-integrations-64bit/tree/main/tools/melcom-galaxy_plugin_updater) to install or update the integration.

1. Download and extract the Plugin Updater.
2. Double-click `update-plugins.bat`.
3. Select your preferred language and follow the displayed instructions.

OAuth credentials are stored outside the plugin folder. Plugin updates do not overwrite this configuration or require it to be restored.

### 📂 Manual Installation

1. Close GOG Galaxy completely, including the system tray application.
2. Download the [latest release package](https://github.com/melcom-creations/galaxy-integration-battlenet/releases/latest).
3. Extract the plugin folder from the ZIP archive into:

   ```text
   %localappdata%\GOG.com\Galaxy\plugins\installed\
   ```

Place `manifest.json` directly inside this folder, without an extra nested plugin folder:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\battlenet_ba170431-0649-482f-863b-d248592f1842\
```

> [!IMPORTANT]
> Do not place backup copies of this plugin inside the `plugins\installed` directory. GOG Galaxy scans every folder inside this directory during startup, so duplicate plugin folders can cause GUID conflicts or load an outdated version.

**Next step:** Continue with [One-Time OAuth Setup (Required)](#-one-time-oauth-setup-required), then [First Start and Initial Sync](#-first-start-and-initial-sync).

## ⚠️ One-Time OAuth Setup (Required)

Complete this setup before connecting for the first time. The shared `CLIENT_ID` and `CLIENT_SECRET` used by the original community plugin have been revoked by Blizzard. You must register your own free OAuth client through the Blizzard Developer Portal.

If OAuth credentials have not been configured, clicking **Connect** in Galaxy opens the setup guide. Enter your Client ID and Client Secret there, then select **Save and Continue** to open the Battle.net login. You do not need to edit a Python file or restart Galaxy.

### 🔑 Registering Your OAuth Client

1. Open the following page and sign in with your Battle.net account:

   [Create a Blizzard API Client](https://develop.battle.net/access/clients/create)

2. Complete the form with the following values:

   | Field | Value |
   | :--- | :--- |
   | **Client Name** | `GOG Galaxy Plugin - MyClient123` |
   | **Redirect URLs** | `http://friendsofgalaxy.com` |
   | **Service URL** | Select `I do not have a service URL for this client` |
   | **Intended Use** | `Personal GOG Galaxy 2.1+ desktop client plugin to display supported Blizzard games and launch them through the Battle.net desktop app. Used locally on my own PC.` |

   The client name must be globally unique across all Blizzard developer accounts. Using only `GOG Galaxy Plugin` will usually fail with a `500 Internal Server Error` because that name has already been registered. Add your username or another unique suffix to the client name.

3. Click **Save** and open the new entry under **Manage Your Clients**.
4. Open **Manage Client -> Credentials**.
5. Copy the displayed **Client ID** and reveal the **Client Secret**.
6. Open **Settings -> Integrations -> Battle.net** in GOG Galaxy and click **Connect**.
7. Enter the **Client ID** and **Client Secret** in the setup window.
8. Click **Save and Continue**.
9. Complete the Battle.net login that opens automatically.

### 🔒 Credential Storage and Disconnect

The setup creates the Battle.net data directory and an `oauth.json` placeholder automatically. On Windows, the file is stored here:

```text
%LOCALAPPDATA%\melcom-creations\GOG Galaxy Integrations\Battle.net\oauth.json
```

Before setup is completed, the file contains only a `setup-required` marker and no credentials. After **Save and Continue**, it contains a Windows DPAPI-protected credential block that can be decrypted only by the same Windows user account on the same computer. Neither the Client ID nor the Client Secret remains in `consts.py` or any other plugin file.

> ⚠️ Keep your Client Secret private. Never publish it, send it to another person, or commit it to a public repository. Anyone with this credential could make API requests using your registered client.

Disconnecting the Battle.net integration removes Galaxy's stored Battle.net login session, but it intentionally keeps `oauth.json`. Your personal Blizzard API client can therefore be reused when you connect again, and plugin updates cannot overwrite it.

To replace or completely remove your personal OAuth configuration, close GOG Galaxy and delete only this file:

```text
%LOCALAPPDATA%\melcom-creations\GOG Galaxy Integrations\Battle.net\oauth.json
```

The guided setup appears again the next time you click **Connect**.

## 🚀 First Start and Initial Sync

For the first synchronization after installing, updating, or configuring the plugin:

1. Start the Battle.net desktop app and keep it open.
2. Start GOG Galaxy.
3. Connect the Battle.net integration through **Settings -> Integrations** if necessary.
4. Open the account menu in the top-right corner and select **Sync integrations**.
5. Wait until the synchronization has finished.

## 🎮 Game Support and Library Notes

### 🔎 Automatic Discovery of Additional Games

Starting with version 2.1.14-64bit, the Windows integration can discover additional installed games using Battle.net's local game information. New installations can appear while Galaxy is running, and discovered games open through Battle.net.

Discovery depends on the information Battle.net provides and GOG's catalog matching. Some games and beta versions may still need a plugin update. Uninstalled purchases still require existing account support.

WoW Forever and The Witcher 3 Remastered have not yet been validated with this version.

### 🎮 World of Warcraft Classic: One Tile, Three Editions

**Classic Era, Mists of Pandaria Classic, and Burning Crusade Classic Anniversary Edition share one "World of Warcraft Classic" tile.** The integration uses GOG's existing Classic catalog entry; separate tiles for these three editions are not supported by this integration with the current catalog mappings.

Click **Play** in Galaxy to open Battle.net, select your edition from the **World of Warcraft Classic** version menu, then click **Play** there. The game does not start automatically. On Windows, all three editions report their running state and combined playtime to the same Galaxy tile. Waiting in Battle.net does not count as playtime.

### 📚 Library Contents After Synchronization

After synchronization, GOG Galaxy displays your purchased Battle.net games together with all supported free-to-play titles known to the plugin. Free-to-play games are shown whether or not you have previously installed or played them. This also applies to titles such as Call of Duty.

During synchronization, entries may temporarily appear as **Unknown game**. If GOG's catalog has no mapping for a reported Battle.net ID, this can persist even when detection and launching work. A verified catalog alias or a catalog correction is then required; waiting or reconnecting alone does not establish the missing mapping.

If you do not want a particular game to appear in your library, right-click its game tile and select **Hide Game**.

### ⚔️ Warcraft III Classic Games

**Warcraft III: Reign of Chaos** and **Warcraft III: The Frozen Throne** appear in GOG Galaxy as not installed. This is intentional.

Blizzard merged both classic games into a single legacy build named **Warcraft III - Legacy TFT 1.29**, which is available through a version selector in the Warcraft III: Reforged launcher. The original installers no longer create dedicated registry entries and instead share the same registry key as Reforged. Using that key would falsely mark the classic games as installed and prevent them from launching correctly.

Clicking **Install** in GOG Galaxy opens the bundled `wc3_classic_info.html` guide. A German version named `wc3_classic_info_DE.html` is also included in the plugin folder.

**Route A - Standalone Launchers:** Download the classic executables from your Blizzard account under **Account Settings -> Games & Subscriptions -> Classic Games**. A registered product key is required for both titles.

**Route B - Battle.net Desktop App:** If you own Warcraft III: Reforged, select Warcraft III in the Battle.net desktop app, open the version selector next to the Play button, and choose **Warcraft III - Legacy TFT 1.29**.

A valid registered product key is required for both routes. Existing keys can be redeemed through the [Battle.net Shop](https://us.shop.battle.net/en-us) under **Profile -> Account Settings -> Account Overview -> Redeem a Code**.

## 🛠️ Troubleshooting

Restart Galaxy and the store app and try one synchronization. If the problem remains, collect a fresh log. A database reset is not required for this.

### 🧪 Create a Fresh Diagnostic Log

1. Close GOG Galaxy completely, including the system tray application.
2. Open `%ProgramData%\GOG.com\Galaxy\logs\`. Move the existing `plugin-battlenet-ba170431-0649-482f-863b-d248592f1842.log` to a backup folder outside this directory, if present. Leave other logs in place.
3. Start the Battle.net desktop app. Start Galaxy, reproduce the problem once, then close Galaxy completely to finish writing the log.
4. Send the newly created plugin log, not the entire folder. Include the plugin and Galaxy versions, your steps, the expected and actual result, and whether the problem can be reproduced.

See [Support & Feedback](#-support--feedback) for contact options.

### 🔄 Reset Plugin Storage (Last Resort)

Use this only if restarting and synchronizing do not help, or when requested for troubleshooting. Cached library data and local playtime may be lost; signing in again may be required. Keep the backup. The separate `oauth.json` file remains unchanged.

1. Close GOG Galaxy completely, including the system tray application.
2. Open `%ProgramData%\GOG.com\Galaxy\storage\plugins\`.
3. Find the active `battlenet_...-storage.db` file for your Galaxy account. If unsure which file is correct, stop. Leave other integrations' databases unchanged.
4. Append `.old` to its name. If that backup already exists, use an unused suffix; never overwrite it.
5. Start the Battle.net desktop app. Start Galaxy, reconnect if necessary, and select **Sync integrations** once. Wait until it finishes.

To undo: close Galaxy, rename the new database to an unused backup name, then restore the saved database's original name. Never restore it while Galaxy is running.

## 🙏 Credits

**Original Community Integration**  
FriendsOfGalaxy, bartok765, and contributors  
[Friends of Galaxy Battle.net integration](https://github.com/FriendsOfGalaxy/galaxy-integration-blizzard)

**64-bit Port, Maintenance and Improvements**  
melcom

## ❤️ Special Thanks

I want to take a moment to thank the people who kept me going during this intense development phase:

* A huge thank you to my friend [**Hustlefan**](https://www.gog.com/u/Hustlefan). Over the past few days, you've been much more than just moral support. You gave me the encouragement I needed, patiently put up with all my Discord spam, and helped beta test the plugins. I'm really happy that you're pleased with the results. Thanks so much for all your support, my friend.

* And a big thank you to my girlfriend [**Florence H.** (fl0H0815)](https://www.gog.com/u/Florence_Heart). While she was enjoying the good life at her parents' place - complete with air conditioning and a huge swimming pool - she kept my spirits up by sending me photos of herself, her friends, her parents, and even her parents' dog. She reminded me that there's a wonderful world outside of a code editor every now and then... 🙈

  *Now that's what I call real support.* ❤️

* Thanks to GOG community member [**jmmontoro**](https://www.gog.com/u/jmmontoro) for pointing out that the suggested client name can cause a `500 Internal Server Error` during Blizzard OAuth registration because every client name must be unique. Adding a personal suffix, such as your username, resolves the problem.

* Thanks to GOG community member [**MacStew**](https://www.gog.com/u/MacStew) for reporting that Diablo IV could no longer be launched through GOG Galaxy after Battle.net stopped accepting the previous game family identifier. His report led to the launch fix in Version 2.1.12-64bit.

Thank you all for having my back!

## 🤝 Support & Feedback

**GitHub Issues are intentionally disabled.** Health-related limitations prevent me from reliably managing separate issue trackers across all of my plugin repositories.

Before contacting me, follow [Troubleshooting](#-troubleshooting) and prepare a fresh Battle.net plugin log with a detailed description.

* **GOG:** Send me a message or add me as a friend through my [GOG profile](https://www.gog.com/u/melcom).
* **Email:** `melcom @ gmx.net`
* **Discord:** `.melcom` - the leading dot is part of the username. You can send me a message or add me as a friend.

Logs can be attached directly or shared using an accessible cloud storage link, such as Dropbox, OneDrive, Google Drive, or a similar service. Response times may vary depending on my health and available development time. Thank you for your understanding.
