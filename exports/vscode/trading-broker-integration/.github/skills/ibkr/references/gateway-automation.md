# Gateway Automation and Production Deployment

Running TWS/IB Gateway unattended on Windows, Linux, macOS or Docker: the outage schedule you must plan around, IBC for login automation, safe auto-start when several bot processes share one Gateway, and the per-platform deployment details. The launcher rules below each encode a distinct failure of unattended operation.

## Scheduled outage windows (plan for both)

- **Daily reset, ~23:45-00:45 ET.** The socket connection ceases to exist (immediate error 502). Restart typically takes 1-5 minutes, but intermittent interruptions can occur throughout the window. Native exchange orders continue to operate; execution reports and simulated orders are delayed.
- **A second connectivity reset around 04:27-04:33 UTC**, reported by operators of multi-client deployments as a daily error-1100 storm hitting every connected client simultaneously. It is not in IBKR's published schedule, so verify it in your own Gateway logs; if you see it, it is scheduled weather rather than your bug.
- **Auto Restart** (Configure -> Lock and Exit -> Auto Restart) restarts TWS/Gateway daily without re-authentication; a manual login is still required weekly, with security tokens invalidating **Sunday at 1:00 AM ET**.
- **Auto-logoff** (the alternative to Auto Restart) defaults to 23:45 local time, configurable via Global Configuration -> Lock and Exit. IBHK-domiciled users are documented as lacking both "Never Lock" and "Auto Restart", so that geography cannot run a week unattended.
- **A username that also logs into Client Portal loses auto-reconnect**: documented, and it looks exactly like a reconnection bug. Keep the bot's username out of the web portal (session-exclusivity rules in `tws-api-architecture.md`).

Design consequence: reconnection logic (see `reconnection-resilience.md`) is not for rare failures; it runs at least daily, at predictable times. Schedule maintenance, backfills, and health-check expectations around both windows.

## IBC: the login automation layer

**IBC** (https://github.com/IbcAlpha/IBC) is the de facto standard for TWS/Gateway automation on every platform (Windows, Linux and macOS release zips), actively maintained (2026 releases added passkey authentication, required by IBKR Japan's mandate, and a `PAUSE` command):

- Automates login with username/password and handles 2FA prompts via IBKR Mobile
- Automatically handles TWS dialog boxes
- Includes **sample XML for Windows Task Scheduler** for daily auto-start
- Command server supports `RECONNECTDATA` (= Ctrl-Alt-F) and `RECONNECTACCOUNT` (= Ctrl-Alt-R)
- Requires the offline/standalone version of TWS
- **Windows note**: use "Run only when user is logged on" in Task Scheduler for interactive access

**IBC is not an IBKR product.** Nothing about it is IBKR-supported, and its own release history is the
reason that matters operationally: version 3.21.0 shipped with a defect its release notes describe as
"a significant problem ... regarding IBC's handling of autorestart. This prevents autorestart from
working with Gateway", telling Gateway users to revert to 3.20.0. The lesson generalises past that one
version: **exercise a full restart cycle on the exact IBC and Gateway pairing you intend to deploy**,
because the component that automates your restarts is the one whose regressions you discover at 23:45.

Config keys worth knowing by name, all in `config.ini`: `AutoRestartTime` (the restart schedule, as an
alternative to setting it in the GUI), `SecondFactorDevice` (which 2FA device to select when several
are enrolled), and the retry triad `ReloginAfterSecondFactorAuthenticationTimeout`,
`SecondFactorAuthenticationExitInterval` and `TWOFA_TIMEOUT_ACTION=restart`, which decide what happens
when a push notification is never acknowledged. IBC documents the retry loop as able to "repeat any
number of times", so a login that is merely slow and one that will never complete look identical to it:
bound the attempts yourself and escalate rather than looping into the session's weekly reauthentication.

## Auto-starting the Gateway under N processes

When several bot processes can each decide "the Gateway is down, start it", the launcher becomes concurrent code with host-wide state. Every rule below encodes a production failure:

- **Single-flight via a host-wide lock.** Acquire with `os.open(path, O_CREAT | O_EXCL)`; exactly one process launches, the others wait on the result. N uncoordinated IBC spawns produce host-wide file locks and login storms.
- **Write the lock payload atomically**: tmp file + `os.replace`, so readers never see a truncated mid-write payload.
- **Stale-lock detection needs PID + process creation time** (`psutil`). A bare `pid_exists()` check is defeated by PID reuse on Windows: a reborn unrelated process holds the "lock" forever.
- **Keep the invariant `LOCK_STALE_SECONDS >= GATEWAY_START_TIMEOUT_SECONDS`** (pin it with a test): a stale-window shorter than a legitimate cold start makes waiters steal the lock mid-launch.
- **A cold IBC login can take 10-15 minutes** (updates, 2FA, warmup). A 90-second start timeout guarantees a crash loop; use >= 600 s.
- **`StartGateway.bat` returns rc=0 one or two seconds after backgrounding the Java process.** "Non-None returncode means failure" is a false positive that puts every process into a restart loop. **Verify startup by probing the API port, never by exit code.**
- **Node-based process managers cannot spawn `.bat` directly** (`spawn EINVAL`); route through `cmd.exe /c`.
- **Detach the Gateway from its spawner** (`DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` on Windows) so a bot restart does not kill the Gateway.
- **Keep the lock file out of world-writable `%TEMP%`** when processes run under a service account; use a dedicated app-state directory.

## Installer channels and filenames

The standalone (offline) builds live under `https://download2.interactivebrokers.com/installers/ibgateway/`,
in a `stable-standalone/` and a `latest-standalone/` channel. Filenames, verified against the host:

| Platform | File |
|---|---|
| Windows | `ibgateway-{channel}-standalone-windows-x64.exe` |
| Linux | `ibgateway-{channel}-standalone-linux-x64.sh` |
| macOS | `ibgateway-{channel}-standalone-macosx-x64.dmg` |

The macOS name is `macosx-x64`, not `macos-x64`; the latter 404s. Prefer `stable` for production, and
know the channels genuinely differ: a 2026-08-13 install measured `stable` shipping build 10.45 while
`latest` was 10.49. The
Linux and Windows installers are install4j-based and take `-q -dir <path>` for unattended installs on
both platforms (InstallBuilder-style `--mode` flags fall back to an interactive GUI); the macOS `.dmg`
must be mounted. Verify an install by the presence of its `jars/` directory, not by the installer's
exit code.

`scripts/ibkr_gateway.py` automates all of this for paper gateways. See `gateway-verification.md`.

## Platform-independent requirements

These apply everywhere and are the ones that actually decide whether unattended operation works.

- **Uncheck Read-Only API before wondering why nothing trades.** IBKR's own configuration lesson states
  that "Read-Only" is **enabled by default** and "will block all API orders. It must be unchecked to
  allow any orders from the API." A fresh Gateway therefore refuses every order until someone changes a
  checkbox, which is the correct default and a guaranteed first-deployment surprise.
- **Bind the API to localhost only.** The API has no authentication worth the name; anything that can
  reach the port can trade.
- **Schedule the restart in the terminal's own time zone.** IBKR states the restart time "is in the time
  zone you have set for TWS", not the host's, so a machine in UTC running a terminal set to US/Eastern
  restarts five hours away from where an operator reading the crontab would expect.
- **Raise the Java heap, inside IBKR's own conflicting band.** Configure, Settings, Memory Allocation.
  IBKR's Knowledge Base recommends 4000 MB for API users while its Users' Guide warns that going above
  about 2000 MB "will likely degrade your machine's overall performance": treat 2-4 GB as the
  documented advisory band and measure on your host rather than trusting either number. Also trim
  Python-side state: `ib_async` bar and ticker objects accumulate.
- **Use the offline/standalone build.** The auto-updater silently changes the terminal under a running
  bot, including its presets.
- **Verify startup by port probe, never by launcher exit code**, and allow 600 s or more for a cold
  login.
- **Give each Gateway its own state directory** and keep launcher lock files out of world-writable
  temp when processes run under a service account.

## Windows

- **Firewall**: Windows Firewall can block the Gateway's Java process. Allow the API ports on
  localhost only:
  ```
  netsh advfirewall firewall add rule name="IB Gateway API" dir=in action=allow protocol=TCP localport=4001,4002 remoteip=127.0.0.1
  ```
- **Antivirus**: some AV products flag TWS. Exclude the installation directory.
- **Task Scheduler + IBC**: run the IBC start script at boot, set "Run only when user is logged on"
  for interactive access, and configure restart-on-failure with a delay.
- **WinError 10038** is a Windows-specific socket error on an improper close:
  ```python
  except OSError as e:
      if getattr(e, "winerror", None) == 10038:  # socket operation on non-socket
          log.warning("WinError 10038: connection already closed")
      else:
          raise
  ```
- Node-based process managers cannot spawn `.bat` directly (`spawn EINVAL`); route through
  `cmd.exe /c`, and detach with `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`.

## Linux

- **Headless needs a virtual display, and IBKR does not support headless at all.** Its own wording is
  that both applications "were designed to require the use of a graphical user interface for secure
  user authentication. For that reason 'headless' operation of either application without a GUI is not
  supported." Running under `xvfb` (`xvfb-run -a ...`), as the Docker images do, satisfies the GUI
  requirement rather than removing it: you are giving the JVM a display it cannot show anyone, not
  running a supported headless mode.
- **systemd** is the natural supervisor. Use `Restart=on-failure`, a `RestartSec` long enough to avoid
  a login storm, and `TimeoutStartSec` at or above the cold-login budget. Run as a dedicated
  unprivileged user with its own home, because the Gateway writes settings under it.
- **Firewall**: bind to loopback. If the process must listen more widely, put it behind an SSH tunnel
  rather than opening the port.
- **Locale and timezone** affect how the terminal renders and parses times. Pin them explicitly; the
  session and reset windows are expressed in exchange time, and a surprising host timezone makes
  schedule reasoning wrong in a way that looks like a venue problem.

## macOS

- Practical for development, rarely the right production host. The `.dmg` install is manual, and
  power management can suspend a machine mid-session.
- If used unattended, disable App Nap and sleep for the Gateway, and prefer `launchd` over cron for
  restart-on-failure semantics.

## Docker

**gnzsnz/ib-gateway-docker** (https://github.com/gnzsnz/ib-gateway-docker) packages IB Gateway plus
IBC, supports live and paper simultaneously, and is actively maintained; its image tags track the
Gateway build.

It is the least surprising deployment for anything not already committed to Windows, because it makes
the terminal version and its configuration explicit and reproducible, which is the single biggest
weakness of a hand-installed Gateway.

The rules above still apply: one starter, port-probe verification, a generous cold-start timeout, and
localhost-only exposure. Two container-specific cautions:

- **The terminal's settings live in a volume.** If that volume is not persisted, presets and
  precaution settings reset on every recreate, silently changing order behaviour. If it *is*
  persisted, it becomes the same unversioned input as a GUI machine. Neither is wrong; the mistake is
  not knowing which one you have.
- **2FA still exists.** Automated restarts do not remove the weekly re-authentication requirement.

## Related

- `gateway-verification.md` -- provisioning a disposable paper Gateway and probing it
- `reconnection-resilience.md` -- what the client does when these windows hit
- `tws-api-architecture.md` -- ports, Gateway-vs-TWS choice, offline build
- `order-lifecycle-contracts.md` -- terminal presets: Gateway config that vetoes API orders
