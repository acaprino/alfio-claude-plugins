# Gateway Automation and Windows Production Deployment

Running TWS/IB Gateway unattended: the outage schedule you must plan around, IBC for login automation, safe auto-start when several bot processes share one Gateway, and the Windows-specific deployment details. Launcher lessons distilled from production incidents on a live multi-strategy FX/metals CFD deployment (retail EU entity).

## Scheduled outage windows (plan for both)

- **Daily reset, ~23:45-00:45 ET.** The socket connection ceases to exist (immediate error 502). Restart typically takes 1-5 minutes, but intermittent interruptions can occur throughout the window. Native exchange orders continue to operate; execution reports and simulated orders are delayed.
- **A second connectivity reset around 04:27-04:33 UTC**, observed in production as a daily error-1100 storm hitting every connected client simultaneously (6 agents x 14 errors each in one incident day). Not in IBKR's published schedule; treat it as expected weather, not an anomaly.
- **Auto Restart** (Configure -> Lock and Exit -> Auto Restart) restarts TWS/Gateway daily without re-authentication; a manual login is still required weekly, with security tokens invalidating **Sunday at 1:00 AM ET**.
- **Auto-logoff** (the alternative to Auto Restart) defaults to 23:45 local time, configurable via Global Configuration -> Lock and Exit.

Design consequence: reconnection logic (see `reconnection-resilience.md`) is not for rare failures; it runs at least daily, at predictable times. Schedule maintenance, backfills, and health-check expectations around both windows.

## IBC: Essential for Windows Production

**IBC** (https://github.com/IbcAlpha/IBC) is the de facto standard for TWS/Gateway automation, actively maintained (2026 releases added passkey authentication, required by IBKR Japan's mandate, and a `PAUSE` command):

- Automates login with username/password and handles 2FA prompts via IBKR Mobile
- Automatically handles TWS dialog boxes
- Includes **sample XML for Windows Task Scheduler** for daily auto-start
- Command server supports `RECONNECTDATA` (= Ctrl-Alt-F) and `RECONNECTACCOUNT` (= Ctrl-Alt-R)
- Requires the offline/standalone version of TWS
- **Windows note**: use "Run only when user is logged on" in Task Scheduler for interactive access

## Auto-starting the Gateway under N processes

When several bot processes can each decide "the Gateway is down, start it", the launcher becomes concurrent code with host-wide state. Every rule below encodes a production failure:

- **Single-flight via a host-wide lock.** Acquire with `os.open(path, O_CREAT | O_EXCL)`; exactly one process launches, the others wait on the result. N uncoordinated IBC spawns produce host-wide file locks and login storms.
- **Write the lock payload atomically**: tmp file + `os.replace`, so readers never see a truncated mid-write payload.
- **Stale-lock detection needs PID + process creation time** (`psutil`). A bare `pid_exists()` check is defeated by PID reuse on Windows: a reborn unrelated process holds the "lock" forever.
- **Keep the invariant `LOCK_STALE_SECONDS >= GATEWAY_START_TIMEOUT_SECONDS`** (pin it with a test): a stale-window shorter than a legitimate cold start makes waiters steal the lock mid-launch.
- **A cold IBC login can take 10-15 minutes** (updates, 2FA, warmup). A 90-second start timeout guarantees a crash loop; use >= 600 s.
- **`StartGateway.bat` returns rc=0 one or two seconds after backgrounding the Java process.** "Non-None returncode means failure" is a false positive that put every process into a PM2 restart loop. **Verify startup by probing the API port, never by exit code.**
- **PM2/Node cannot spawn `.bat` directly** (`spawn EINVAL`); route through `cmd.exe /c`.
- **Detach the Gateway from its spawner** (`DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` on Windows) so a bot restart does not kill the Gateway.
- **Keep the lock file out of world-writable `%TEMP%`** when processes run under a service account; use a dedicated app-state directory.

## Windows production deployment

### Firewall rules

Windows Firewall can block TWS/Gateway's Java process. Create inbound rules for API ports (7496/7497/4001/4002). Only allow localhost connections:

```
netsh advfirewall firewall add rule name="IB Gateway API" dir=in action=allow protocol=TCP localport=4001,4002 remoteip=127.0.0.1
```

### Antivirus

Some AV solutions flag TWS as suspicious. Add the TWS/Gateway installation directory to exclusions.

### Memory

Increase the Java heap (Configure -> Settings -> Memory Allocation; 4096 MB is a battle-tested floor for high data volumes) to prevent crashes. Monitor Python memory as well -- ib_async bar/ticker objects accumulate over time and must be trimmed.

### WinError 10038

Windows-specific socket error when the connection closes improperly. Handle in exception catching:

```python
except OSError as e:
    if e.winerror == 10038:  # Socket operation on non-socket
        log.warning("WinError 10038: connection already closed")
    else:
        raise
```

### Task Scheduler + IBC

The standard combination for automated Windows deployment:
1. Create a Task Scheduler task to run IBC startup script at system boot
2. Set "Run only when user is logged on" for interactive access
3. Configure restart on failure with appropriate delay
4. IBC handles Gateway login, 2FA, and daily restart

### Docker alternative

**gnzsnz/ib-gateway-docker** (https://github.com/gnzsnz/ib-gateway-docker) packages IB Gateway + IBC, supports simultaneous live+paper, and is actively maintained. The launcher rules above still apply conceptually (one starter, port-probe verification, generous cold-start timeout).

## Related

- `reconnection-resilience.md` -- what the client does when these windows hit
- `tws-api-architecture.md` -- ports, Gateway-vs-TWS choice, offline build
- `order-lifecycle-contracts.md` -- terminal presets: Gateway config that vetoes API orders
