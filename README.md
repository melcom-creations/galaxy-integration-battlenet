# Battle.net Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This repository contains the Battle.net (Blizzard) integration plugin for the 64-bit version of GOG Galaxy 2.1+.

The original community integration has been updated to work with the current 64-bit GOG Galaxy client and Python 3.13. In addition to compatibility improvements, this project includes a restored OAuth authentication flow using personal Blizzard developer credentials, an updated protobuf game database, dependency updates, bug fixes, stability improvements, and ongoing maintenance.

---

## ✨ Features

* Compatible with GOG Galaxy 2.1+ (64-bit)
* Python 3.13 support
* Updated 64-bit dependencies
* Restored OAuth authentication via a personal Blizzard developer client
* Regenerated protobuf database compatible with `protobuf >= 4.x` / Python 3.13
* Guided one-time setup page (`setup.html`) displayed inside GOG Galaxy
* Expanded game definitions including Diablo IV
* Warcraft III classic games handled correctly — no false "installed" state, dedicated local guide included
* Classic 32-bit game detection restored on 64-bit Windows
* Instant login window (region pre-warming eliminates the startup delay)
* Local playtime tracking with commercial rounding for all Battle.net games
* Ongoing maintenance and bug fixes

---

## ⚠️ Mandatory One-Time Setup

> **This step is required before the plugin can authenticate. It cannot be skipped.**

The original shared `CLIENT_ID` and `CLIENT_SECRET` used by the community plugin have been revoked by Blizzard. You must register your own free OAuth client at the Blizzard Developer Portal.

**The plugin guides you through this automatically.** When `CLIENT_ID` and `CLIENT_SECRET` in `consts.py` are empty, GOG Galaxy displays the bundled `setup.html` page inside the client every time you click **Connect** — until both values have been filled in.

### How to register your OAuth client

1. Open the following URL in your browser and sign in with your Battle.net account:

   ```text
   https://develop.battle.net/access/clients/create
   ```

2. Fill in the form with these values:

   | Field | Value |
   |---|---|
   | **Client Name** | `GOG Galaxy Plugin` (or any name you prefer) |
   | **Redirect URLs** | `http://friendsofgalaxy.com` |
   | **Service URL** | Check *"I do not have a service URL for this client"* |
   | **Intended Use** | `Personal GOG Galaxy 2.0 desktop client plugin to display owned Blizzard games and launch them via the Battle.net launcher. Only used locally on my own PC.` |

3. Click **Save**. You will be redirected to **Manage Your Clients**. Click your new entry to open it, then navigate to **Manage Client → Credentials**. Your **Client ID** is shown there directly. Click **Show Secret** to reveal your **Client Secret**.

4. Open `consts.py` in the plugin folder:

   ```text
   %LOCALAPPDATA%\GOG.com\Galaxy\plugins\installed\battlenet_ba170431-0649-482f-863b-d248592f1842\
   ```

   Replace the two placeholder lines:

   ```python
   CLIENT_ID = "your_client_id_here"
   CLIENT_SECRET = "your_client_secret_here"
   ```

5. **Fully close and reopen GOG Galaxy.** The plugin reads `consts.py` only on startup — changes do not take effect until you restart.

6. Go to **Settings → Integrations → Battle.net** and click **Connect**.

> ⛔ Keep your `CLIENT_SECRET` private. Never share it publicly or commit it to a public repository. Anyone with this key can make API calls on your behalf.

---

## 📦 Installation

### Standard Installation (Recommended)

1. Close GOG Galaxy completely (including the system tray icon).
2. Download the latest release from this repository.
3. Open the following folder:

   ```text
   %LOCALAPPDATA%\GOG.com\Galaxy\plugins\installed\
   ```

4. Extract the ZIP archive **directly into this folder**.

The resulting directory structure **must** look like this:

```text
%LOCALAPPDATA%\GOG.com\Galaxy\plugins\installed\
└── battlenet_ba170431-0649-482f-863b-d248592f1842\
    ├── manifest.json
    ├── plugin.py
    ├── consts.py
    ├── setup.html
    ├── README.md
    └── ...
```

5. Open `consts.py` and enter your personal `CLIENT_ID` and `CLIENT_SECRET` (see [Mandatory One-Time Setup](#️-mandatory-one-time-setup) above).
6. Start GOG Galaxy.

### If the plugin folder is missing

If a future ZIP archive does **not** already contain the folder

```text
battlenet_ba170431-0649-482f-863b-d248592f1842
```

perform the following steps:

1. Open:

   ```text
   %LOCALAPPDATA%\GOG.com\Galaxy\plugins\installed\
   ```

2. Create a new folder named exactly:

   ```text
   battlenet_ba170431-0649-482f-863b-d248592f1842
   ```

3. Extract **all files from the ZIP archive into this newly created folder**.

The final directory structure must match the one shown above.

---

## 🔄 Resetting the Plugin Database (Recommended)

If the plugin behaves unexpectedly after an update, resetting the local plugin database is recommended.

1. Open:

   ```text
   C:\ProgramData\GOG.com\Galaxy\storage\plugins\
   ```

2. Locate all files beginning with:

   ```text
   battlenet_
   ```

   and ending with:

   ```text
   -storage.db
   ```

3. Rename each database by appending `.old` to its filename.

   Example:

   ```text
   battlenet_xxxxxxxxx-storage.db
   ```

   becomes

   ```text
   battlenet_xxxxxxxxx-storage.db.old
   ```

4. Start GOG Galaxy again.
5. Reconnect the Battle.net integration if necessary.

---

## ⚔️ Warcraft III Classic Games

**Warcraft® III: Reign of Chaos®** and **Warcraft® III: The Frozen Throne®** appear in GOG Galaxy as **not installed**. This is intentional.

Blizzard merged both classics into a single legacy build called **Warcraft III – Legacy TFT 1.29**, accessible inside the Reforged launcher via a version dropdown. Their original installer no longer creates a dedicated registry entry — it now shares the same key as Warcraft III: Reforged. Detecting them via the registry would therefore always resolve to the Reforged install path and falsely mark them as installed, which would prevent them from launching correctly.

Clicking **Install** in GOG Galaxy opens `wc3_classic_info.html`, a local guide that explains your two options for playing them. A German version (`wc3_classic_info_DE.html`) is also included in the plugin folder.

**Route A – Standalone launchers:** Download the classic executables directly from your Blizzard account page under *Account Settings → Games & Subscriptions → Classic Games*. This requires a registered product key for both titles.

**Route B – Battle.net launcher:** If you own Warcraft III: Reforged, open the Battle.net launcher, select Warcraft III, click the dropdown next to the Play button and choose **Warcraft III – Legacy TFT 1.29**.

> ⚠️ A valid, registered product key is required for both routes. Keys can be redeemed at [us.shop.battle.net](https://us.shop.battle.net/en-us) → Profile icon → Account Settings → Account Overview → Redeem a Code.

---

## ⚠️ Known Limitations

**Some unowned Free-to-Play games appear in your library.**

Blizzard's `/api/games-and-subs` endpoint is restricted to internal first-party applications and returns HTTP 401 for any externally registered OAuth client. The plugin therefore cannot distinguish between games you have purchased and games that are free-to-play for everyone. All F2P titles in the database (StarCraft, StarCraft II, World of Warcraft, Hearthstone, Heroes of the Storm, Diablo Immortal, Warcraft Rumble, Call of Duty titles, etc.) will appear in your library regardless of ownership.

**Workaround:** Right-click any unwanted game in GOG Galaxy → **Hide**.

---

## ⚠️ Important

Do **not** place backup copies of this plugin inside the `plugins\installed` directory.

GOG Galaxy scans every folder inside this directory during startup. Duplicate plugin folders can lead to GUID conflicts or cause Galaxy to load an outdated version of the plugin.

---

## 🙏 Credits

**Original Community Integration**
FriendsOfGalaxy, bartok765, and contributors
https://github.com/FriendsOfGalaxy/galaxy-integration-blizzard

**64-bit Port, Maintenance and Improvements**
melcom

---

## ❤️ Special Thanks

I want to take a moment to thank the people who kept me going during this intense development phase:

* A huge thank you to my friend [**Hustlefan**](https://www.gog.com/u/Hustlefan). Over the past few days, you've been much more than just moral support. You gave me the encouragement I needed, patiently put up with all my Discord spam, and helped beta test the plugins. I'm really happy that you're pleased with the results. Thanks so much for all your support, my friend.

* And a big thank you to my girlfriend [**Florence H.** (fl0H0815)](https://www.gog.com/u/Florence_Heart). While she was enjoying the good life at her parents' place - complete with air conditioning and a huge swimming pool - she kept my spirits up by sending me photos of herself, her friends, her parents, and even her parents' dog. She reminded me that there's a wonderful world outside of a code editor every now and then... 🙈

  *Now that's what I call real support.* ❤️

Thank you both for having my back!

---

## 🤝 Support & Feedback

This project is developed and maintained by one person. Response times may vary, especially during periods when health-related limitations reduce available development time.

**GitHub Issues are intentionally disabled.**

If you would like to report a bug or suggest an improvement, please use the contact form on my website:

📩 https://melcom-creations.github.io/melcom-music/contact.html

Thank you for your patience and support!
