# Battle.net Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This repository contains the Battle.net integration plugin for the native 64-bit version of GOG Galaxy 2.1+. It is based on the original community integration and has been updated for the current GOG Galaxy client and Python 3.13. The project includes a restored OAuth authentication flow, an updated game database, compatibility fixes, stability improvements, and ongoing maintenance.

---

## ✨ Features

* Imports purchased Battle.net games into GOG Galaxy
* Includes supported free-to-play Battle.net titles
* Detects locally installed Battle.net games
* Launches, installs, and uninstalls games through the Battle.net desktop app
* Tracks local game time for Battle.net games
* Uses personal Blizzard developer credentials for OAuth authentication
* Includes a guided one-time setup page inside GOG Galaxy
* Supports current game definitions, including Diablo IV
* Restores detection of classic 32-bit games on 64-bit Windows
* Handles Warcraft III classic titles without falsely marking them as installed
* Supports GOG Galaxy 2.1+ 64-bit and Python 3.13

---

## 📦 Installation

### Automatic Installation with Plugin Updater (Recommended)

The easiest way to install the Battle.net integration is with the [melcom GOG Galaxy Plugin Updater](https://github.com/melcom-creations/galaxy-integrations-64bit/tree/main/tools/melcom-galaxy_plugin_updater). The updater detects existing integrations and can install any supported melcom plugins that are still missing.

1. Download and extract the Plugin Updater.
2. Double-click `update-plugins.bat`.
3. Select your preferred language.
4. Follow the displayed instructions.

When updating an existing Battle.net installation, the updater detects personal credentials in `consts.py`, creates an additional backup, and offers to restore the file after the update.

### Manual Installation

1. Close GOG Galaxy completely and make sure it is no longer running in the system tray.
2. Download the latest release package from this repository.
3. Extract the ZIP archive directly into:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
```

The resulting directory structure must look like this:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
└── battlenet_ba170431-0649-482f-863b-d248592f1842\
    ├── manifest.json
    ├── plugin.py
    ├── consts.py
    ├── setup.html
    ├── README.md
    └── ...
```

4. Complete the mandatory OAuth setup below.

---

## ⚠️ Mandatory One-Time OAuth Setup

This step is required before the plugin can authenticate and cannot be skipped. The shared `CLIENT_ID` and `CLIENT_SECRET` used by the original community plugin have been revoked by Blizzard. You must register your own free OAuth client through the Blizzard Developer Portal.

When `CLIENT_ID` and `CLIENT_SECRET` in `consts.py` are empty, GOG Galaxy displays the bundled `setup.html` guide whenever you click **Connect**. The setup page remains available until both values have been entered.

### Registering Your OAuth Client

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
6. Open `consts.py` in:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\battlenet_ba170431-0649-482f-863b-d248592f1842\
```

7. Replace the two placeholder values:

```python
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
```

8. Save `consts.py`.
9. Fully close and reopen GOG Galaxy because the plugin reads this file only during startup.
10. Open **Settings -> Integrations -> Battle.net** and click **Connect**.

> ⚠️ Keep your `CLIENT_SECRET` private. Never publish it, send it to another person, or commit it to a public repository. Anyone with this credential could make API requests using your registered client.

---

## 🚀 First Start and Initial Sync

For the first synchronization after installing, updating, or configuring the plugin:

1. Start the Battle.net desktop app and keep it open.
2. Start GOG Galaxy.
3. Connect the Battle.net integration through **Settings -> Integrations** if necessary.
4. Open the account menu in the top-right corner and select **Sync integrations**.
5. Wait until the synchronization has finished.

---

## 🎮 Library Contents After Synchronization

After synchronization, GOG Galaxy displays your purchased Battle.net games together with all supported free-to-play titles known to the plugin. Free-to-play games are shown whether or not you have previously installed or played them. This also applies to titles such as Call of Duty.

During the initial synchronization, one or more entries may temporarily appear as **Unknown game**. These entries usually resolve or disappear automatically over time as GOG Galaxy processes the imported data. Once this has completed, the library should contain your purchased games and the supported free-to-play titles.

If you do not want a particular game to appear in your library, right-click its game tile and select **Hide Game**.

---

## ⚔️ Warcraft III Classic Games

**Warcraft III: Reign of Chaos** and **Warcraft III: The Frozen Throne** appear in GOG Galaxy as not installed. This is intentional.

Blizzard merged both classic games into a single legacy build named **Warcraft III - Legacy TFT 1.29**, which is available through a version selector in the Warcraft III: Reforged launcher. The original installers no longer create dedicated registry entries and instead share the same registry key as Reforged. Using that key would falsely mark the classic games as installed and prevent them from launching correctly.

Clicking **Install** in GOG Galaxy opens the bundled `wc3_classic_info.html` guide. A German version named `wc3_classic_info_DE.html` is also included in the plugin folder.

**Route A - Standalone Launchers:** Download the classic executables from your Blizzard account under **Account Settings -> Games & Subscriptions -> Classic Games**. A registered product key is required for both titles.

**Route B - Battle.net Desktop App:** If you own Warcraft III: Reforged, select Warcraft III in the Battle.net desktop app, open the version selector next to the Play button, and choose **Warcraft III - Legacy TFT 1.29**.

A valid registered product key is required for both routes. Existing keys can be redeemed through the [Battle.net Shop](https://us.shop.battle.net/en-us) under **Profile -> Account Settings -> Account Overview -> Redeem a Code**.

---

## 🔄 Resetting the Plugin Database (Troubleshooting)

Reset the local plugin database only if the integration behaves unexpectedly or synchronization problems continue after restarting both applications.

1. Close GOG Galaxy completely.
2. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`.
3. Find every file starting with `battlenet_` and ending in `-storage.db`.
4. Rename each matching file by appending `.old`, for example:

   `battlenet_xxxxxxxxx-storage.db` -> `battlenet_xxxxxxxxx-storage.db.old`

5. Start the Battle.net desktop app and keep it open.
6. Start GOG Galaxy and reconnect the Battle.net integration if necessary.
7. Open the account menu in the top-right corner and select **Sync integrations**.
8. Wait until the synchronization has finished.

---

## ⚠️ Important

Do **not** place backup copies of this plugin inside the `plugins\installed` directory.

GOG Galaxy scans every folder inside this directory during startup. Duplicate plugin folders can lead to GUID conflicts or cause Galaxy to load an outdated version of the plugin.

Never share `consts.py` with another person. This file can contain your personal Blizzard OAuth credentials.

---

## 🙏 Credits

**Original Community Integration**  
FriendsOfGalaxy, bartok765, and contributors  
[Friends of Galaxy Battle.net integration](https://github.com/FriendsOfGalaxy/galaxy-integration-blizzard)

**64-bit Port, Maintenance and Improvements**  
melcom

---

## ❤️ Special Thanks

I want to take a moment to thank the people who kept me going during this intense development phase:

* A huge thank you to my friend [**Hustlefan**](https://www.gog.com/u/Hustlefan). Over the past few days, you've been much more than just moral support. You gave me the encouragement I needed, patiently put up with all my Discord spam, and helped beta test the plugins. I'm really happy that you're pleased with the results. Thanks so much for all your support, my friend.

* And a big thank you to my girlfriend [**Florence H.** (fl0H0815)](https://www.gog.com/u/Florence_Heart). While she was enjoying the good life at her parents' place - complete with air conditioning and a huge swimming pool - she kept my spirits up by sending me photos of herself, her friends, her parents, and even her parents' dog. She reminded me that there's a wonderful world outside of a code editor every now and then... 🙈

  *Now that's what I call real support.* ❤️

* Thanks to GOG community member [**jmmontoro**](https://www.gog.com/u/jmmontoro) for pointing out that the suggested client name can cause a `500 Internal Server Error` during Blizzard OAuth registration because every client name must be unique. Adding a personal suffix, such as your username, resolves the problem.

Thank you all for having my back!

---

## 🤝 Support & Feedback

This project is developed and maintained by one person. Response times may vary, especially during periods when health-related limitations reduce available development time.

**GitHub Issues are intentionally disabled.**

If you would like to report a bug or suggest an improvement, please use the contact form on my website:

📩 [Contact form](https://melcom-creations.github.io/melcom-music/contact.html)

Thank you for your patience and support!
