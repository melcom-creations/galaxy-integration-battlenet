# Battle.net Integration for GOG Galaxy 2.1+ (64-bit)

**Current Version: 2.1.7-64bit**

This repository contains the Battle.net community integration for the 64-bit version of GOG Galaxy 2.1+.

The project has been modernized to work with the current 64-bit GOG Galaxy client and Python 3.13. It includes compatibility fixes, regenerated protocol files, updated 64-bit dependencies, stability improvements, and ongoing maintenance.

---

## ✨ Features

- Compatible with GOG Galaxy 2.1+ (64-bit)
- Python 3.13 support
- Updated 64-bit native dependencies
- Restored classic game detection on 64-bit Windows
- Modernized OAuth authentication for Battle.net
- Regenerated `product_db_pb2.py` for current protobuf support
- Guided setup flow for first-time configuration
- Warcraft III Classic helper pages included in the repository

---

## Setup Flow

This plugin includes a local `setup.html` page that is opened inside GOG Galaxy during the first login or connect flow while the plugin is still missing valid OAuth credentials.

The setup page will continue to appear until you enter valid values for `CLIENT_ID` and `CLIENT_SECRET` in `consts.py`. After those values are set, the setup page is no longer called.

The repository also includes `wc3_classic_info.html` for Warcraft III Classic games, and `wc3_classic_info_DE.html` is included for German users.

---

## Requirements: Your Own Blizzard OAuth Client

> Important: this is a mandatory one-time setup step.

The original shared Battle.net OAuth credentials used by older community integrations are no longer valid. You must create your own free OAuth client before the plugin can authenticate.

1. Go to `https://develop.battle.net` and log in with your Battle.net account.
2. Open `API Access -> Manage Your Clients -> Create Client`.
3. Fill in the form:
   - Client Name: `GOG Galaxy Plugin` or any name you prefer
   - Redirect URLs: `http://friendsofgalaxy.com`
   - Enable `I do not have a service URL for this client`
   - Intended Use: `Personal GOG Galaxy 2.0 desktop client plugin to display owned Blizzard games and launch them via the Battle.net launcher. Only used locally on my own PC.`
4. Save the client.
5. Open `consts.py` in the plugin folder and replace the placeholder values:
   ```python
   CLIENT_ID = "your_client_id_here"
   CLIENT_SECRET = "your_client_secret_here"
   ```

Keep `CLIENT_SECRET` private. Do not share it publicly.

---

## 📦 Installation

### Standard Installation

1. Close GOG Galaxy completely, including the system tray icon.
2. Download the latest release ZIP from this repository.
3. Open this folder:
   ```text
   %localappdata%\GOG.com\Galaxy\plugins\installed\
   ```
4. Extract the ZIP archive directly into the folder named:
   ```text
   battlenet_ba170431-0649-482f-863b-d248592f1842
   ```
5. Open `consts.py` and enter your personal `CLIENT_ID` and `CLIENT_SECRET`.
6. Start GOG Galaxy again.

The final directory structure should look like this:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
└── battlenet_ba170431-0649-482f-863b-d248592f1842\
    ├── manifest.json
    ├── plugin.py
    ├── README.md
    ├── setup.html
    ├── wc3_classic_info.html
    ├── wc3_classic_info_DE.html
    └── ...
```

### If the plugin folder is missing

If a future ZIP archive does not already contain the folder
```text
battlenet_ba170431-0649-482f-863b-d248592f1842
```
create that folder first, then extract all files from the ZIP archive into it.

---

## 🔄 Resetting the Plugin Database

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
3. Rename each database by appending `.old` to the filename.

Example:
```text
battlenet_xxxxxxxxx-storage.db
```
becomes:
```text
battlenet_xxxxxxxxx-storage.db.old
```

4. Start GOG Galaxy again.
5. Reconnect the Battle.net integration if needed.

---

## ⚠️ Important

Do not place backup copies of this plugin inside the `plugins\installed` directory.

GOG Galaxy scans every folder inside this directory during startup. Duplicate plugin folders can lead to GUID conflicts or cause Galaxy to load an outdated version of the plugin.

---

## 🙏 Credits

**Original Community Integration**  
Friends of Galaxy  
https://github.com/FriendsOfGalaxy/galaxy-integration-steam

**Authorization Flow Contributions**  
ABaumher  
https://github.com/ABaumher

**64-bit Port, Maintenance and Improvements**  
melcom

---

## 📚 References

This integration is based on and inspired by several open-source projects and community resources.

- https://github.com/SteamRE/SteamKit
- https://github.com/ValuePython/steam
- https://github.com/prncc/steam-scraper
- https://github.com/rhaarm/steam-scraper
- https://github.com/mulhod/steam_reviews
- https://github.com/summersb92/aeolipile
- https://github.com/rcpoison/steam-scraper
- https://github.com/chmccc/steam-scraper

---

## ❤️ Special Thanks

I want to take a moment to thank the people who kept me going during this intense development phase:

- A huge thank you to my friend [**Hustlefan**](https://www.gog.com/u/Hustlefan). Over the past few days, you have been much more than just moral support. You gave me the encouragement I needed, patiently put up with all my Discord spam, and helped beta test the plugins. I am really happy that you are pleased with the results. Thank you so much for all your support, my friend.

- And a big thank you to my girlfriend [**Florence H.** (fl0H0815)](https://www.gog.com/u/Florence_Heart). While she was enjoying the good life at her parents' place - complete with air conditioning and a huge swimming pool - she kept my spirits up by sending me photos of herself, her friends, her parents, and even her parents' dog. She reminded me that there is a wonderful world outside of a code editor every now and then.

  Now that is what I call real support.

Thank you both for having my back!

---

## 🤝 Support & Feedback

This project is developed and maintained by one person. Response times may vary, especially during periods where health-related limitations reduce available development time.

GitHub Issues are intentionally disabled.

If you would like to report a bug or suggest an improvement, please use the contact form on my website:

https://melcom-creations.github.io/melcom-music/contact.html

Thank you for your patience and support!
