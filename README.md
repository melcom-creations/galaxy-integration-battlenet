# Battle.net Integration for GOG Galaxy 2.1+ (64-bit)

**Current Version: 2.1.3-64bit**

This repository provides a fully modernized, 64-bit compatible Battle.net (Blizzard) community integration for GOG Galaxy 2.1+. It resolves every known incompatibility between the legacy 32-bit plugin and the current 64-bit GOG Galaxy client running Python 3.13, restores OAuth authentication using a personal Blizzard developer client, regenerates the protobuf game database for modern library support, and ships native 64-bit compiled dependencies.

For a complete technical breakdown of all changes, see [CHANGELOG.md](CHANGELOG.md).

---

## What this repository provides

- A fully 64-bit compatible Battle.net integration for GOG Galaxy 2.1+
- Working OAuth authentication via a personal Blizzard developer client (the original shared credentials were revoked by Blizzard)
- Regenerated `product_db_pb2.py` compatible with `protobuf >= 4.x` / Python 3.13
- Bundled, precompiled native 64-bit Python 3.13 C-extensions required by the plugin
- A rebuilt game definitions database with modern Blizzard and Activision titles including Diablo IV
- Classic 32-bit game detection restored on 64-bit Windows/Python
- Warcraft III classic games (Reign of Chaos & The Frozen Throne) handled correctly — no false "installed" state, guided setup page included
- Instant login window (region pre-warming eliminates the 3–4 second delay on first connect)
- Guided one-time setup page (`setup.html`) that appears inside GOG Galaxy when the plugin is not yet configured

---

## Requirements: Your Own Blizzard OAuth Client

> ⚠️ **This is a mandatory one-time setup step.**

The original shared `CLIENT_ID` and `CLIENT_SECRET` used by the community plugin have been revoked by Blizzard. You must register your own free OAuth client before the plugin can authenticate.

1. Go to [https://develop.battle.net](https://develop.battle.net) and log in with your Battle.net account.
2. Navigate to **API Access → Manage Your Clients → Create Client**.
3. Fill in the form:
   - **Client Name:** `GOG Galaxy Plugin` (or anything you like)
   - **Redirect URLs:** `http://friendsofgalaxy.com`
   - Check **"I do not have a service URL for this client"**
   - **Intended Use:** `Personal GOG Galaxy 2.0 desktop client plugin to display owned Blizzard games and launch them via the Battle.net launcher. Only used locally on my own PC.`
4. Click **Save**. You will receive a **Client ID** and a **Client Secret**.
5. Open `consts.py` in the plugin folder and replace the values:
   ```python
   CLIENT_ID = "your_client_id_here"
   CLIENT_SECRET = "your_client_secret_here"
   ```

> 💡 Keep your `CLIENT_SECRET` private. Never share it publicly.

---

## Installation

### Step 1: Install the 64-bit Plugin Files

Because this fix includes new 64-bit compiled dependencies, you **must** overwrite the entire plugin folder, not just the `.py` files.

1. **Fully close** GOG Galaxy (including the system tray icon).
2. Download the latest release `.zip` from this repository.
3. Navigate to your GOG community plugins folder:
   `%localappdata%\GOG.com\Galaxy\plugins\installed\`
4. Find the folder named `battlenet_ba170431-0649-482f-863b-d248592f1842`.
5. Delete the contents of this folder and extract the downloaded `.zip` into it.
6. Open `consts.py` and enter your personal `CLIENT_ID` and `CLIENT_SECRET` (see above).

### Step 2: Reset the Local Cache Database (Mandatory)

The game database has been significantly expanded. You must reset the local GOG Galaxy cache to allow it to rebuild correctly.

1. Navigate to:
   `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`
   *(or paste `%ProgramData%\GOG.com\Galaxy\storage\plugins\` into the Windows search bar)*
2. Find files starting with `battlenet_` and ending with `-storage.db`.
3. Rename them by appending `.old` (e.g. `battlenet_ba170431...-storage.db.old`).
4. Launch GOG Galaxy, go to **Settings → Integrations** and connect your Battle.net account.

---

## Warcraft III Classic Games

**Warcraft® III: Reign of Chaos®** and **Warcraft® III: The Frozen Throne®** appear in GOG Galaxy as **not installed**. This is intentional.

Blizzard merged both classics into a single legacy build called **Warcraft III – Legacy TFT 1.29**, accessible inside the Reforged launcher via a version dropdown. Their original installer no longer creates a dedicated registry entry — it now shares the same key as Warcraft III: Reforged. Detecting them via the registry would therefore always return the Reforged install path and falsely mark them as installed, which would prevent them from launching at all.

Clicking **Install** in GOG Galaxy will open `wc3_classic_info.html`, a local guide that explains your two options for playing them:

- **Route A – Standalone launchers:** Download the classic executables directly from your Blizzard account page under *Account Settings → Games & Subscriptions → Classic Games*. This requires a registered product key for both titles.
- **Route B – Battle.net launcher:** If you own Warcraft III: Reforged, open the Battle.net launcher, select Warcraft III, click the dropdown next to the Play button and choose **Warcraft III – Legacy TFT 1.29**.

> ⚠️ A valid, registered product key is required for both routes. Keys can be redeemed at [us.shop.battle.net](https://us.shop.battle.net/en-us) → Profile icon → Account Settings → Account Overview → Redeem a Code.

---

## Known Limitations

**Some unowned Free-to-Play games appear in your library.**

Blizzard's `/api/games-and-subs` endpoint is restricted to internal first-party applications and returns HTTP 401 for any externally registered OAuth client. The plugin therefore cannot distinguish between games you have purchased and games that are free-to-play for everyone. All F2P titles in the database (StarCraft, StarCraft II, World of Warcraft, Hearthstone, Heroes of the Storm, Diablo Immortal, Warcraft Rumble, Call of Duty titles, etc.) will appear in your library regardless of ownership.

**Workaround:** Right-click any unwanted game in GOG Galaxy → **Hide**.

---

## Credits & Support

* **Original Plugin Authors:** FriendsOfGalaxy, bartok765, and contributors ([GitHub Repository](https://github.com/FriendsOfGalaxy/galaxy-integration-blizzard))
* **Based on the galaxy-integration-blizzard 1.4.3 codebase:** FriendsOfGalaxy and contributors to that release
* **64-bit Port, OAuth Fix, Modernization & Continued Development:** melcom

Questions, issues or feedback:

* [https://www.melcom-music.de/contact.html](https://www.melcom-music.de/contact.html)
* Discord: **.melcom** (note the leading dot)

*Have fun and happy gaming!*