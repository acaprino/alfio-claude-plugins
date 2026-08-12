#!/usr/bin/env python3
"""Provision a disposable IB Gateway for paper-account verification.

Downloads the IB Gateway standalone build and IBC, installs both unattended where the
platform allows it, writes an IBC configuration pinned to paper trading, starts the
Gateway headless and verifies it by probing the API port.

Paper only, by construction. The live API ports are refused, the configured trading mode
is forced to `paper`, and `ibkr_probe.py` independently re-checks the account prefix after
connecting. Provisioning a live Gateway is deliberately not supported here: use your real
deployment tooling for that.

Stdlib only. No third-party imports, so it runs before anything is installed.

Usage:
    python ibkr_gateway.py doctor
    python ibkr_gateway.py download [--channel stable|latest]
    python ibkr_gateway.py install  [--channel stable|latest]
    python ibkr_gateway.py configure --user <ibkr-paper-username>
    python ibkr_gateway.py start [--port 4002] [--timeout 900]
    python ibkr_gateway.py probe --port 4002
    python ibkr_gateway.py stop
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

GATEWAY_BASE = "https://download2.interactivebrokers.com/installers/ibgateway"
IBC_API = "https://api.github.com/repos/IbcAlpha/IBC/releases/latest"

# Installer filenames verified against the download host on 2026-08-12.
# Note macOS is "macosx-x64", not "macos-x64"; the latter 404s.
INSTALLER_NAME = {
    "Windows": "ibgateway-{channel}-standalone-windows-x64.exe",
    "Linux": "ibgateway-{channel}-standalone-linux-x64.sh",
    "Darwin": "ibgateway-{channel}-standalone-macosx-x64.dmg",
}

IBC_ASSET = {"Windows": "IBCWin", "Linux": "IBCLinux", "Darwin": "IBCMacos"}

# Live ports. Refused outright; this tool provisions paper gateways only.
LIVE_PORTS = {4001, 7496}
PAPER_GATEWAY_PORT = 4002

UA = {"User-Agent": "Mozilla/5.0 (compatible; ibkr-trading-plugin)"}


def workdir() -> Path:
    """Per-user state directory. Never inside the repository, never world-writable temp."""
    env = os.environ.get("IBKR_VERIFY_HOME")
    if env:
        return Path(env).expanduser()
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "ibkr-verify"


def info(msg: str) -> None:
    print(f"[ibkr-gateway] {msg}", flush=True)


def die(msg: str, code: int = 1) -> "NoReturn":  # type: ignore[valid-type]
    print(f"[ibkr-gateway] ERROR: {msg}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def guard_port(port: int) -> int:
    if port in LIVE_PORTS:
        die(
            f"port {port} is a LIVE trading port. This tool provisions paper gateways only. "
            f"Paper defaults: {PAPER_GATEWAY_PORT} (Gateway), 7497 (TWS)."
        )
    return port


def download(url: str, dest: Path, label: str) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        info(f"{label} already present ({dest.stat().st_size / 1e6:.0f} MB): {dest}")
        return dest
    info(f"downloading {label} from {url}")
    req = urllib.request.Request(url, headers=UA)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(req) as resp, open(tmp, "wb") as fh:
            total = int(resp.headers.get("Content-Length") or 0)
            done = 0
            last = 0.0
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
                done += len(chunk)
                now = time.time()
                if total and now - last > 2:
                    print(f"    {done / 1e6:7.0f} / {total / 1e6:.0f} MB", flush=True)
                    last = now
    except urllib.error.HTTPError as exc:
        die(f"download failed for {url}: HTTP {exc.code}")
    except urllib.error.URLError as exc:
        die(f"download failed for {url}: {exc.reason}")
    tmp.replace(dest)
    info(f"{label} downloaded: {dest} ({dest.stat().st_size / 1e6:.0f} MB)")
    return dest


def gateway_installer_url(channel: str) -> tuple[str, str]:
    system = platform.system()
    name = INSTALLER_NAME.get(system)
    if not name:
        die(f"unsupported platform: {system}")
    fname = name.format(channel=channel)
    return f"{GATEWAY_BASE}/{channel}-standalone/{fname}", fname


def ibc_asset_url() -> tuple[str, str]:
    import json

    req = urllib.request.Request(IBC_API, headers=UA)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except Exception as exc:  # noqa: BLE001
        die(f"could not query the IBC release API: {exc}")
    prefix = IBC_ASSET[platform.system()]
    for asset in data.get("assets", []):
        if asset["name"].startswith(prefix):
            return asset["browser_download_url"], asset["name"]
    die(f"no IBC asset matching {prefix} in release {data.get('tag_name')}")


def cmd_download(args: argparse.Namespace) -> None:
    root = workdir()
    url, fname = gateway_installer_url(args.channel)
    download(url, root / "downloads" / fname, "IB Gateway installer")
    ibc_url, ibc_name = ibc_asset_url()
    download(ibc_url, root / "downloads" / ibc_name, "IBC")
    info("download complete")


def cmd_install(args: argparse.Namespace) -> None:
    root = workdir()
    cmd_download(args)
    _, fname = gateway_installer_url(args.channel)
    installer = root / "downloads" / fname
    gw_dir = root / "ibgateway"
    system = platform.system()

    if system == "Linux":
        installer.chmod(installer.stat().st_mode | stat.S_IEXEC)
        info(f"installing IB Gateway unattended into {gw_dir}")
        run = subprocess.run(
            [str(installer), "-q", "-dir", str(gw_dir)],
            capture_output=True,
            text=True,
        )
        if run.returncode != 0:
            die(f"installer exited {run.returncode}: {run.stderr.strip()[:400]}")
    elif system == "Windows":
        info(f"installing IB Gateway unattended into {gw_dir}")
        run = subprocess.run(
            [str(installer), "--mode", "unattended", "--prefix", str(gw_dir)],
            capture_output=True,
            text=True,
        )
        if run.returncode != 0:
            die(f"installer exited {run.returncode}: {run.stderr.strip()[:400]}")
    else:
        die(
            f"macOS ships a .dmg that needs mounting and is not scripted here.\n"
            f"  Mount it and drag IB Gateway to /Applications:\n"
            f"    open {installer}\n"
            f"  Then re-run: ibkr_gateway.py configure ..."
        )

    _, ibc_name = ibc_asset_url()
    ibc_zip = root / "downloads" / ibc_name
    ibc_dir = root / "ibc"
    info(f"extracting IBC into {ibc_dir}")
    ibc_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ibc_zip) as zf:
        zf.extractall(ibc_dir)
    for script in ibc_dir.rglob("*.sh"):
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
    info("install complete")


def cmd_configure(args: argparse.Namespace) -> None:
    root = workdir()
    cfg = root / "config.ini"
    password = os.environ.get("IB_PASSWORD", "")
    if not password:
        info(
            "IB_PASSWORD is not set. Writing the config without it; either export "
            "IB_PASSWORD before starting, or edit the file by hand."
        )
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        "\n".join(
            [
                "# Generated by ibkr_gateway.py. Paper trading is pinned on purpose.",
                "IbLoginId=" + args.user,
                "IbPassword=" + password,
                "TradingMode=paper",
                "IbDir=" + str(root / "ibgateway"),
                "OverrideTwsApiPort=" + str(guard_port(args.port)),
                "AcceptIncomingConnectionAction=accept",
                "AcceptNonBrokerageAccountWarning=yes",
                "ReadOnlyApi=no",
                "ExistingSessionDetectedAction=primary",
                "LogComponents=never",
                "",
            ]
        ),
        encoding="utf-8",
    )
    try:
        cfg.chmod(0o600)
    except OSError:
        pass
    info(f"wrote {cfg} (mode 600 where supported)")
    if password:
        info("the password is stored in that file: it is outside the repository, keep it that way")


def port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def cmd_probe(args: argparse.Namespace) -> None:
    port = guard_port(args.port)
    ok = port_open(args.host, port)
    print(f"{args.host}:{port} {'OPEN' if ok else 'CLOSED'}")
    raise SystemExit(0 if ok else 2)


def cmd_start(args: argparse.Namespace) -> None:
    root = workdir()
    port = guard_port(args.port)
    cfg = root / "config.ini"
    if not cfg.exists():
        die(f"no config at {cfg}. Run: ibkr_gateway.py configure --user <paper-username>")

    if port_open(args.host, port):
        info(f"port {port} already open; a Gateway appears to be running. Nothing to do.")
        return

    ibc_dir = root / "ibc"
    system = platform.system()
    if system == "Windows":
        candidates = list(ibc_dir.rglob("StartGateway.bat"))
        if not candidates:
            die(f"StartGateway.bat not found under {ibc_dir}. Run: ibkr_gateway.py install")
        cmd = ["cmd.exe", "/c", str(candidates[0])]
        creationflags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        popen_kw = {"creationflags": creationflags}
    else:
        candidates = list(ibc_dir.rglob("gatewaystart.sh"))
        if not candidates:
            die(f"gatewaystart.sh not found under {ibc_dir}. Run: ibkr_gateway.py install")
        cmd = [str(candidates[0])]
        popen_kw = {"start_new_session": True}

    env = dict(os.environ)
    env["TWS_MAJOR_VRSN"] = env.get("TWS_MAJOR_VRSN", "1030")
    env["IBC_INI"] = str(cfg)
    env["TRADING_MODE"] = "paper"

    info(f"launching: {' '.join(cmd)}")
    logfile = root / "gateway-launch.log"
    with open(logfile, "ab") as fh:
        subprocess.Popen(cmd, stdout=fh, stderr=fh, env=env, **popen_kw)  # noqa: S603

    # The launcher backgrounds the JVM and returns rc=0 within a second or two. Its exit
    # code says nothing about whether the Gateway came up. Verify by probing the port.
    deadline = time.time() + args.timeout
    info(f"waiting up to {args.timeout}s for {args.host}:{port} (a cold login can take 10-15 min)")
    while time.time() < deadline:
        if port_open(args.host, port):
            info(f"API port {port} is open")
            return
        time.sleep(5)
    die(
        f"port {port} did not open within {args.timeout}s. Check {logfile} and the IBC logs. "
        f"A first login often needs 2FA confirmation on IBKR Mobile."
    )


def cmd_stop(_: argparse.Namespace) -> None:
    system = platform.system()
    if system == "Windows":
        subprocess.run(
            ["taskkill", "/F", "/FI", "WINDOWTITLE eq IB Gateway*"],
            capture_output=True,
            text=True,
        )
        subprocess.run(["taskkill", "/F", "/IM", "javaw.exe"], capture_output=True, text=True)
    else:
        subprocess.run(["pkill", "-f", "ibgateway"], capture_output=True, text=True)
        subprocess.run(["pkill", "-f", "IBController"], capture_output=True, text=True)
    info("stop signalled; re-probe the port to confirm")


def cmd_doctor(args: argparse.Namespace) -> None:
    root = workdir()
    print(f"platform          : {platform.system()} {platform.machine()}")
    print(f"python            : {sys.version.split()[0]}")
    print(f"state directory   : {root}  {'(exists)' if root.exists() else '(absent)'}")
    print(f"gateway installed : {(root / 'ibgateway').exists()}")
    print(f"IBC installed     : {(root / 'ibc').exists()}")
    print(f"config written    : {(root / 'config.ini').exists()}")
    print(f"IB_PASSWORD set   : {bool(os.environ.get('IB_PASSWORD'))}")
    try:
        import ib_async  # noqa: F401

        print(f"ib_async          : {ib_async.__version__}")
    except Exception:  # noqa: BLE001
        print("ib_async          : NOT INSTALLED  (pip install 'ib_async<3.0.0')")
    for port, label in ((4002, "Gateway paper"), (7497, "TWS paper")):
        print(f"port {port} ({label:13}): {'OPEN' if port_open(args.host, port) else 'closed'}")
    for port in sorted(LIVE_PORTS):
        state = "OPEN" if port_open(args.host, port) else "closed"
        print(f"port {port} (LIVE         ): {state}   <- never targeted by this tool")
    print(f"java on PATH      : {shutil.which('java') or 'not found (Gateway bundles its own)'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name, fn in (("download", cmd_download), ("install", cmd_install)):
        p = sub.add_parser(name)
        p.add_argument("--channel", default="stable", choices=("stable", "latest"))
        p.set_defaults(func=fn)

    p = sub.add_parser("configure")
    p.add_argument("--user", required=True, help="IBKR paper-account username")
    p.add_argument("--port", type=int, default=PAPER_GATEWAY_PORT)
    p.set_defaults(func=cmd_configure)

    p = sub.add_parser("start")
    p.add_argument("--port", type=int, default=PAPER_GATEWAY_PORT)
    p.add_argument("--timeout", type=int, default=900, help="cold IBC logins can take 10-15 minutes")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("probe")
    p.add_argument("--port", type=int, default=PAPER_GATEWAY_PORT)
    p.set_defaults(func=cmd_probe)

    sub.add_parser("stop").set_defaults(func=cmd_stop)
    sub.add_parser("doctor").set_defaults(func=cmd_doctor)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
