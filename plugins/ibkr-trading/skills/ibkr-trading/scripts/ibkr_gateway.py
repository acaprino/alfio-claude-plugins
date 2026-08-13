#!/usr/bin/env python3
"""Provision a disposable IB Gateway for paper-account verification.

Downloads the IB Gateway standalone build and IBC, installs both unattended where the
platform allows it, writes an IBC configuration pinned to paper trading, starts the
Gateway headless through IBC's service entry points and verifies it by probing the API
port.

Paper only, by construction. The live API ports are refused, the configured trading mode
is forced to `paper` on the IBC command line AND in the config file, and `ibkr_probe.py`
independently re-checks the account prefix after connecting. Provisioning a live Gateway
is deliberately not supported here: use your real deployment tooling for that.

Launching goes through IBC's `scripts/ibcstart.sh` / `scripts\\StartIBC.bat`, never the
top-level `gatewaystart.sh` / `StartGateway.bat`: the top-level launchers are user-editable
config files that hard-assign TWS_MAJOR_VRSN, CONFIG/IBC_INI, TRADING_MODE and IBC_PATH,
so nothing passed via the environment survives them. The service scripts take everything
as explicit arguments.

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
import http.client
import os
import platform
import shutil
import signal
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

# IBC locates the Gateway at <tws-path>/ibgateway/<version>/ and uses the version number
# only to build that path and for numeric feature gates. The channel installers carry no
# version in their filename, so we install into a fixed, deliberately high pseudo-version:
# every "version >= N" gate in IBC's scripts passes, and no guessing of the real build
# number is needed. The real version is whatever the chosen channel shipped.
GW_VERSION_DIR = "10000"

# Live ports. Refused outright; this tool provisions paper gateways only. This is defence
# in depth: the substantive guard is ibkr_probe.py re-checking the account prefix after
# connecting, because any port number can be pointed at any gateway.
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


def tws_path() -> Path:
    return workdir() / "Jts"


def gateway_dir() -> Path:
    return tws_path() / "ibgateway" / GW_VERSION_DIR


def settings_dir() -> Path:
    return workdir() / "tws-settings"


def pid_file() -> Path:
    return workdir() / "gateway.pid"


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
    total = 0
    done = 0
    try:
        with urllib.request.urlopen(req) as resp, open(tmp, "wb") as fh:
            total = int(resp.headers.get("Content-Length") or 0)
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
    except (urllib.error.URLError, http.client.IncompleteRead) as exc:
        tmp.unlink(missing_ok=True)
        die(f"download failed for {url}: {exc}")
    # A connection that closes early without raising must not cache a truncated file:
    # a partial 330 MB installer would be reported "already present" forever after.
    if total and done != total:
        tmp.unlink(missing_ok=True)
        die(f"download truncated: got {done} of {total} bytes for {url}; re-run")
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

    system = platform.system()
    prefix = IBC_ASSET.get(system)
    if not prefix:
        die(f"unsupported platform: {system}")
    req = urllib.request.Request(IBC_API, headers=UA)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except Exception as exc:  # noqa: BLE001
        die(f"could not query the IBC release API: {exc}")
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


def _downloaded_ibc_zip(root: Path) -> Path:
    candidates = sorted((root / "downloads").glob("IBC*.zip"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        die("no IBC zip in the downloads directory. Run: ibkr_gateway.py download")
    return candidates[0]


def cmd_install(args: argparse.Namespace) -> None:
    root = workdir()
    cmd_download(args)
    _, fname = gateway_installer_url(args.channel)
    installer = root / "downloads" / fname
    gw_dir = gateway_dir()
    system = platform.system()

    if system == "Darwin":
        die(
            f"macOS ships a .dmg that needs mounting and is not scripted here.\n"
            f"  Mount it and install IB Gateway into: {gw_dir}\n"
            f"    open {installer}\n"
            f"  Then re-run: ibkr_gateway.py configure ..."
        )

    # The Gateway installer is install4j-based on both platforms; -q -dir is its
    # unattended vocabulary (InstallBuilder-style --mode flags fall back to a GUI).
    if system == "Linux":
        installer.chmod(installer.stat().st_mode | stat.S_IEXEC)
    info(f"installing IB Gateway unattended into {gw_dir}")
    gw_dir.parent.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(
        [str(installer), "-q", "-dir", str(gw_dir)],
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        die(f"installer exited {run.returncode}: {run.stderr.strip()[:400]}")
    # install4j launchers can return before the install completes; trust the tree,
    # not the exit code. IBC itself hard-fails without a jars directory.
    if not (gw_dir / "jars").is_dir():
        die(f"install finished but {gw_dir / 'jars'} does not exist; the installer "
            f"likely ignored -dir. Inspect {installer} and the installer log.")

    ibc_zip = _downloaded_ibc_zip(root)
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
                "OverrideTwsApiPort=" + str(guard_port(args.port)),
                # accept is required for an unattended prober; exposure is capped by the
                # Gateway's localhost-only default and by this being a paper session.
                "AcceptIncomingConnectionAction=accept",
                "AcceptNonBrokerageAccountWarning=yes",
                "ReadOnlyApi=no",
                # secondary: if a session already exists elsewhere, THIS throwaway
                # gateway terminates rather than killing a session the user relies on.
                "ExistingSessionDetectedAction=secondary",
                "LogStructureWhen=never",
                "",
            ]
        ),
        encoding="utf-8",
    )
    try:
        cfg.chmod(0o600)
    except OSError:
        pass
    info(f"wrote {cfg} (chmod 600 attempted; on Windows your user-profile ACLs apply)")
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


def _ibc_service_script(ibc_dir: Path) -> Path:
    name = "StartIBC.bat" if platform.system() == "Windows" else "ibcstart.sh"
    candidates = list(ibc_dir.rglob(name))
    if not candidates:
        die(f"{name} not found under {ibc_dir}. Run: ibkr_gateway.py install")
    return candidates[0]


def cmd_start(args: argparse.Namespace) -> None:
    root = workdir()
    port = guard_port(args.port)
    cfg = root / "config.ini"
    if not cfg.exists():
        die(f"no config at {cfg}. Run: ibkr_gateway.py configure --user <paper-username>")
    if not (gateway_dir() / "jars").is_dir():
        die(f"no Gateway install at {gateway_dir()}. Run: ibkr_gateway.py install")

    if port_open(args.host, port):
        info(
            f"WARNING: port {port} is already open, but this tool did not start that "
            f"process and cannot vouch for what it is. Confirm it is a paper gateway "
            f"before using it: python ibkr_probe.py capabilities --stock AAPL"
        )
        return

    settings_dir().mkdir(parents=True, exist_ok=True)
    script = _ibc_service_script(root / "ibc")
    system = platform.system()

    # IBC's SERVICE entry points take everything as arguments. The top-level
    # gatewaystart.sh / StartGateway.bat would overwrite TWS_MAJOR_VRSN, CONFIG/IBC_INI,
    # TRADING_MODE and IBC_PATH with their own hard-coded values, silently dropping the
    # paper pin, so they are deliberately not used here.
    if system == "Windows":
        cmd = [
            "cmd.exe", "/c", str(script), GW_VERSION_DIR, "/G",
            f"/TwsPath:{tws_path()}",
            f"/TwsSettingsPath:{settings_dir()}",
            f"/IbcPath:{root / 'ibc'}",
            f"/Config:{cfg}",
            "/Mode:paper",
        ]
        popen_kw = {"creationflags": 0x00000008 | 0x00000200}  # DETACHED | NEW_GROUP
    else:
        if system == "Linux" and not os.environ.get("DISPLAY"):
            die(
                "no DISPLAY: IB Gateway is a Java GUI app even when run 'headless'. "
                "Run under a virtual display, e.g.: xvfb-run -a python ibkr_gateway.py start"
            )
        cmd = [
            str(script), GW_VERSION_DIR, "--gateway",
            f"--tws-path={tws_path()}",
            f"--tws-settings-path={settings_dir()}",
            f"--ibc-path={root / 'ibc'}",
            f"--ibc-ini={cfg}",
            "--mode=paper",
        ]
        popen_kw = {"start_new_session": True}

    info(f"launching: {' '.join(cmd)}")
    logfile = root / "gateway-launch.log"
    with open(logfile, "ab") as fh:
        proc = subprocess.Popen(cmd, stdout=fh, stderr=fh, **popen_kw)  # noqa: S603
    pid_file().write_text(str(proc.pid), encoding="utf-8")

    # Launchers background the JVM and exit quickly; their exit code says nothing about
    # whether the Gateway came up. Verify by probing the API port.
    deadline = time.time() + args.timeout
    info(f"waiting up to {args.timeout}s for {args.host}:{port} (a cold login can take 10-15 min)")
    while time.time() < deadline:
        if port_open(args.host, port):
            info(f"API port {port} is open")
            return
        time.sleep(5)
    die(
        f"port {port} did not open within {args.timeout}s. Check {logfile} and the IBC logs "
        f"under {root / 'ibc'}. A first login often needs 2FA confirmation on IBKR Mobile."
    )


def cmd_stop(_: argparse.Namespace) -> None:
    """Stop the Gateway THIS tool started. Never touches other Java processes."""
    system = platform.system()
    stopped = False

    pf = pid_file()
    if pf.exists():
        try:
            pid = int(pf.read_text().strip())
        except ValueError:
            pid = 0
        if pid > 0:
            if system == "Windows":
                run = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                                     capture_output=True, text=True)
                stopped = run.returncode == 0
            else:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                    stopped = True
                except (ProcessLookupError, PermissionError, OSError):
                    stopped = False
        pf.unlink(missing_ok=True)

    if not stopped:
        # Fallback: match IBC's Gateway entry point AND this tool's state directory on
        # the command line, so a production Gateway or any other JVM is never touched.
        marker = workdir().name  # "ibkr-verify" (or the IBKR_VERIFY_HOME basename)
        if system == "Windows":
            for image in ("java.exe", "javaw.exe"):
                subprocess.run(
                    ["wmic", "process", "where",
                     f"name='{image}' and commandline like '%ibcalpha.ibc.IbcGateway%' "
                     f"and commandline like '%{marker}%'",
                     "call", "terminate"],
                    capture_output=True, text=True)
        else:
            subprocess.run(["pkill", "-f", f"ibcalpha\\.ibc\\.IbcGateway.*{marker}"],
                           capture_output=True, text=True)
        info("no recorded PID; sent a scoped terminate (IbcGateway + this tool's state dir)")
    info("stop signalled; re-probe the port to confirm")


def cmd_doctor(args: argparse.Namespace) -> None:
    root = workdir()
    system = platform.system()
    print(f"platform          : {system} {platform.machine()}")
    print(f"python            : {sys.version.split()[0]}")
    print(f"state directory   : {root}  {'(exists)' if root.exists() else '(absent)'}")
    print(f"gateway installed : {(gateway_dir() / 'jars').is_dir()}  ({gateway_dir()})")
    print(f"IBC installed     : {(root / 'ibc').exists()}")
    print(f"config written    : {(root / 'config.ini').exists()}")
    print(f"IB_PASSWORD set   : {bool(os.environ.get('IB_PASSWORD'))}")
    if system == "Linux":
        print(f"DISPLAY           : {os.environ.get('DISPLAY') or 'NOT SET (use xvfb-run)'}")
        print(f"Xvfb on PATH      : {bool(shutil.which('Xvfb'))}")
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
