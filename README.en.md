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

### Easy way: download the program (recommended)

1. Go to **[Releases](../../releases/latest)** and download **`ControlCelular.exe`**. It's a single file; you don't
   need Python or anything else.
2. Double-click it. You can keep it in any folder, even Downloads.
   - Windows may show **"Windows protected your PC"** because the program isn't signed. Tap **More info → Run
     anyway**.
   - The first time, it asks whether to **open the firewall** (only for your home network) and, if your network is
     "Public", whether to mark it as **private**. Answer **Y**, only if it's your home network, and accept Windows'
     prompt.
   - If **ViGEmBus** (the virtual controller driver) is missing, it asks **"Install it now?"**. Answer **Y**, accept
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

Open **Control Celular**. The window shows a **QR code**, the address and the pairing code. The **controller icon**
next to the Windows clock has: show the QR code, show or hide the window, start with Windows, paired phones (to
forget them), version and uninstall, and exit.

### On the phone (the first time)

1. **Scan the QR code** with your phone's camera.
2. Follow that page's steps to install the **certificate** (needed for the app and the gyro). Each phone has its own
   steps:
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
| The phone can't open the page | Make sure the PC and the phone are on the **same network**. Close and reopen Control Celular and answer **Y** to open the firewall and mark the network as private. |
| "ViGEmBus driver is missing" | Answer **Y** when the program offers to install it, or do it manually from [ViGEmBus releases](https://github.com/nefarius/ViGEmBus/releases). If it still isn't detected, restart your PC. |
| "Windows protected your PC" | The program isn't signed. Tap **More info → Run anyway**, or use the Python option. |
| The certificate isn't detected (iPhone) | Check you used **Safari** and turned on **full trust** (Settings → General → About → Certificate Trust Settings). |
| It doesn't work on café, university or hotel WiFi | Those networks don't let devices see each other, and the controller doesn't open ports on public networks on purpose. Use your phone's hotspot. |
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
