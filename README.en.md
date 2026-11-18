# Control Celular

*[Leer en español](README.md)*

Use your **Android phone or iPhone as a game controller for your PC**. Windows, Steam and emulators see it as a
**real Xbox 360 controller** (or a **DualShock 4**), as if it were plugged in via USB.

- Works over your **home WiFi**, with low delay and no internet needed.
- A lightweight web page that installs as an app; it runs fine on low-end phones.
- Three kinds of controller:
  - **full** (Xbox style);
  - **sideways remote** (one hand, held sideways);
  - **per game**: it reads your Steam library and builds a controller for each kind of game.
- **Gyro** (steering, aiming, and real DualShock 4 motion), **vibration** (Android), **up to 4 players**, and an
  **editor** to move, resize, recolor and change any button, with **turbo** and **toggle** buttons.
- Available in **English and Spanish**: it follows your phone's and Windows' language.

---

## What you need

| | |
|---|---|
| **PC** | Windows 10 or 11 |
| **Phone** | Android with Chrome, or iPhone with Safari |
| **Network** | The PC and the phone on the **same network** (your home WiFi, or your phone's hotspot) |
| **Driver** | **ViGEmBus**: it creates the virtual controller. **It's included**: if you don't have it, the program offers to install it. |

---

## Install on the PC

### Easy way: the installer (recommended)

1. Go to **[Releases](../../releases/latest)** and download **`ControlCelular-Instalar-….exe`**.
2. Open it and click **Next → Install**. Windows asks for permission once, and the installer sets everything up:
   it installs **ViGEmBus** if missing, opens the firewall only for Control Celular and only for your home network
   (whether Windows has it as "Private" or "Public"), removes any Windows block, and creates the icons. If you had an older version, it
   replaces it and (checkbox on by default) deletes old installers and portable versions from Downloads and
   Desktop. Your settings are kept.
3. When it finishes, Control Celular opens and shows the QR code: **scan it with your phone and play**.

To uninstall: Settings → Apps → Control Celular (it also removes the firewall rules and the autostart).

### Portable: no install

1. In **[Releases](../../releases/latest)** download **`ControlCelular.exe`**: a single file.
2. Double-click it. You can keep it in any folder, even Downloads.
   - Windows may show **"Windows protected your PC"** because the program isn't signed. Tap **More info → Run
     anyway**.
   - The first time, it asks whether to **open the firewall** (only for your home network). Click **Yes** and accept
     Windows' prompt.
   - If **ViGEmBus** (the virtual controller driver) is missing, it asks **"Install it now?"**. Click **Yes**, accept
     Windows' prompt and click **Install** in its installer. It's included: the official installer, signed by its
     author. When it finishes, Control Celular opens again by itself.

### With Python (if you want to see or change the code)

1. Install **Python 3.10 or newer** from [python.org/downloads](https://www.python.org/downloads/) and tick **"Add
   python.exe to PATH"**.
2. Download the project (**Code → Download ZIP**) and unzip it, or use `git clone`.
3. Run **`iniciar.bat`**. The first time it installs everything by itself.

To build your own `ControlCelular.exe`, run **`construir.bat`** (it ends up in `dist\`).

---

## Use it

### On the PC (every time)

Open **Control Celular**. The neon controller lights up in the middle of the screen and then the **Control Celular
window** opens: the **QR code**, the pairing code and the address (with a copy button), the **4 player slots** (which
phone is in each one, and whether the PC sees it as Xbox 360 or DualShock 4), the open **Steam game**, the **paired
phones** (with **Forget**), the **activity** log, and **⚙ Options** (open when the PC starts, new-version alerts,
and **Turn off**).

If you close the window, Control Celular **keeps running** in the **controller icon** next to the Windows clock:
click it (or open the program again) to bring the window back. The icon's menu also has: start with Windows, paired
phones, version and uninstall, and exit.

### On the phone: with the Android app (recommended)

The app works in any home because it connects in three ways:

| Way | How | When |
|---|---|---|
| 📶 **WiFi** | The app finds the PC by itself: tap its name. | Phone and PC on the same network. |
| 🔌 **USB cable** | Plug the phone into the PC and turn on **“USB tethering”** (the app has a button that takes you there). The PC shows up in the list. | If the router doesn't let devices see each other, or for the lowest delay. |
| 🔵 **Bluetooth** | Tap **Connect via Bluetooth** with Control Celular open on the PC: they connect by themselves. | If the PC has Bluetooth and you don't want cables. |

1. On the PC, in the Control Celular window, **📱 Android app** tab: scan the QR code and get `ControlCelular.apk`
   (also on **[Releases](../../releases/latest)**, or at `http://<PC IP>:8765/app.apk` if the phone has no internet).
2. Open the file. The first time Android asks you to **allow installing apps from this source**: accept and tap
   **Install**. Play Protect may warn because the app isn't on Google Play: tap **Install anyway**.
3. Open **Control Celular** on the phone, pick your PC (or Bluetooth) and enter the **code** shown on the PC the first
   time. After that it connects by itself.

With the app you don't need the certificate: gyro and vibration always work.

### On the phone: no app, from the browser (and on iPhone)

1. **Scan the QR code** with your phone's camera: **you land straight on the controller** and it pairs by itself.
2. **Optional:** to install it as an app and use the gyro, open **☰ → Enable app and gyro** and install the
   **certificate**. Each phone has its own steps:
   - **Android:** the page detects your brand (Samsung, Xiaomi, Motorola…) and shows the exact path in Settings.
   - **iPhone:** use **Safari**. The certificate installs as a **profile**, and afterwards you must **turn on full
     trust** in Settings → General → About → Certificate Trust Settings.
3. If you came from the QR code, it **pairs automatically**.
4. Install it as an app:
   - **Android:** ☰ → **Install app**.
   - **iPhone:** in Safari tap **Share** → **Add to Home Screen**.

Afterwards you open the app and it connects by itself. At the top you'll see a **green** dot, your **player number**
and the **delay** in milliseconds.

### What's different on iPhone

iPhone gets its own version of the controller page (separate files, so it never interferes with Android):

- **No vibration:** Safari doesn't let web pages vibrate.
- **Gyro:** iPhone asks for permission. Tap **Allow** in ⚙ Settings → Gyro.
- **Install:** with **Add to Home Screen** (there's no full-screen button; the installed app already opens in full
  screen).

> The iPhone version follows how Safari works, but it **hasn't been tested on a real iPhone yet**. If something
> doesn't work, please open an issue.

---

## The two buttons at the top: ⚙ Settings and ☰ Menu

**☰ Menu** (choose and do):
- **Choose your controller:** Full (Xbox), Sideways remote, PS4 (DualShock 4: big touchpad, PS button,
  △ ○ ✕ □ and both sticks at the bottom; the PC sees it as a DualShock 4), or Per game (Steam). Per game shows your installed games;
  tap one to build a controller for its kind (racing, shooter, platformer, sports, fighting or full).
- **Controller editor:** move, resize, change shape, color, what each button sends and its text; add buttons,
  sticks and D-pads; undo and grid; each button can be **normal**, **⚡ turbo** or **📌 toggle**.
- **Copy settings from another phone**, **Show tutorial**, **Full screen** and **Install app**.

**⚙ Settings** (a window with tabs):
- **General:** vibration (Android), night mode, left-handed mode, **The PC sees it as** (Xbox 360 or DualShock 4) and
  **Language**.
- **Gyro:** steering wheel (left stick), aim (right stick) or **real motion** (DualShock 4: works with Steam Input's
  gyro and emulators like Cemu or Yuzu); sensitivity and invert.
- **Sticks:** dead zone, response and travel for each stick.

Everything is saved per phone, on the PC too: if the PC's IP changes or you reinstall the app, you get it all back.

---

## Common problems

| Problem | Try this |
|---|---|
| The phone can't open the page | Make sure the PC and the phone are on the **same network**. Close and reopen Control Celular and click **Yes** to open the firewall. |
| The phone says `ERR_CONNECTION_TIMED_OUT` | Something blocks the connection between phone and PC: usually an **antivirus with its own firewall** (Avast, AVG, Norton, McAfee, Kaspersky, ESET…). Allow Control Celular in it, or briefly pause it to confirm. With no antivirus, it may be the router: try your phone's hotspot. |
| "An Application Control policy has blocked this file" (code 4551) | It's Windows 11 **Smart App Control**: it blocks unsigned programs with no way to run them anyway. Turn it off in Windows Security → App & browser control → Smart App Control → **Off**. Note: Windows won't let you turn it back on (unless you reinstall Windows); the PC stays protected by Microsoft Defender. |
| "ViGEmBus driver is missing" | Click **Yes** when the program offers to install it, or do it manually from [ViGEmBus releases](https://github.com/nefarius/ViGEmBus/releases). If it still isn't detected, restart your PC. |
| "Windows protected your PC" | The program isn't signed. Tap **More info → Run anyway**, or use the Python option. |
| The certificate isn't detected (iPhone) | Check you used **Safari** and turned on **full trust** (Settings → General → About → Certificate Trust Settings). |
| It doesn't work on café, university or hotel WiFi | Those networks don't let devices see each other. Use your phone's hotspot. |
| The game doesn't detect the controller | Open Control Celular **before** the game. In Steam: Settings → Controller. |

---

## Security

- Everything runs **on your local network**. The only thing it does on the internet is check this project's public
  Releases page for new versions (you can turn it off from the icon).
- A phone needs the **pairing code** (shown only on your screen, also inside the QR code) to connect. After 5 wrong
  codes a device is blocked for a while, and the code changes if there are too many failed attempts.
- The certificate is created by your own PC and is **restricted to private network addresses**: it can't be used to
  impersonate any website.
- You can **forget** any paired phone from the icon.

---

## Third-party software

Control Celular includes, unmodified, the official installer of **[ViGEmBus](https://github.com/nefarius/ViGEmBus)**
by Nefarius Software Solutions e.U., under the BSD 3-Clause License. Full notice in
[`terceros/LICENCIA-ViGEmBus.txt`](terceros/LICENCIA-ViGEmBus.txt).

## License

[MIT](LICENSE). What's new in each version: [NOVEDADES.md](NOVEDADES.md) (in Spanish).
