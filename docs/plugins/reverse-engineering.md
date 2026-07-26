# Reverse Engineering Plugin

> Binary reverse engineering, malware analysis, firmware security, and software protection research. Three specialist agents plus four reference skills covering binary patterns, anti-reversing techniques, memory forensics, and network protocol analysis. Scoped for authorized security research, CTF competitions, and defensive security work.

**Version:** 1.1.1 (marketplace 9.0.0)

## Agents

### `reverse-engineer`

Expert reverse engineer for binary analysis, disassembly, decompilation, and protocol extraction. Masters IDA Pro, Ghidra, radare2, x64dbg, and modern RE toolchains.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Binary analysis, CTF challenges, security research, understanding undocumented software, library inspection, executable analysis |

**Invocation:**
```
Use the reverse-engineer agent to analyze [binary path or scenario]
```

**Coverage:**
- Static and dynamic analysis workflows
- Disassembly and decompilation across x86, x86-64, ARM, RISC-V
- Control flow recovery, code pattern recognition, anti-analysis evasion handling
- Library inspection, symbol recovery, type inference
- Protocol extraction from compiled clients
- References the `binary-analysis-patterns` and `anti-reversing-techniques` skills

---

### `malware-analyst`

Defensive malware analyst specializing in threat intelligence, incident response, and sandbox-based behavioral analysis.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Malware triage, threat hunting, incident response, IOC extraction, family identification |

**Invocation:**
```
Use the malware-analyst agent to triage [sample path or behavior description]
```

**Coverage:**
- Static analysis: PE/ELF/Mach-O headers, imports, strings, YARA rules
- Dynamic analysis: sandbox execution, syscall tracing, network observation
- Unpacking, deobfuscation, persistence mechanism identification
- Malware family attribution and threat-actor tracking
- IOC extraction (hashes, C2 domains, mutex names, persistence keys)
- References the `memory-forensics`, `binary-analysis-patterns`, and `anti-reversing-techniques` skills

---

### `firmware-analyst`

Embedded systems and IoT security expert for firmware extraction, analysis, and vulnerability research.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Firmware security audits, IoT penetration testing, embedded systems research, hardware reverse engineering |

**Invocation:**
```
Use the firmware-analyst agent to audit [firmware image or device description]
```

**Coverage:**
- Firmware extraction from flash dumps, OTA packages, vendor portals
- Filesystem and bootloader unpacking (binwalk, squashfs, jffs2, ubifs)
- Cross-architecture analysis (ARM Cortex-M/A, MIPS, RISC-V, PowerPC)
- Hardware interface attacks (UART, JTAG, SWD, SPI/I2C flash readout)
- Vulnerability research on routers, IoT devices, automotive ECUs, industrial controllers
- References the `binary-analysis-patterns` and `anti-reversing-techniques` skills

---

## Skills

### `binary-analysis-patterns`

Master reference for disassembly, decompilation, control flow analysis, and code pattern recognition. Use when analyzing executables, understanding compiled code, or performing static analysis on binaries.

---

### `anti-reversing-techniques`

Understanding anti-reversing, obfuscation, and protection techniques encountered during software analysis. Triggers on malware evasion analysis, anti-debugging implementation for CTFs, packed binary analysis, and detection of virtualized environments.

**Reference files:**
- `advanced-techniques.md` — extended coverage of advanced obfuscation, anti-VM, and anti-emulation patterns

---

### `memory-forensics`

Memory acquisition, process analysis, and artifact extraction using Volatility and related tools. Triggers on memory dump analysis, incident investigation, and malware analysis from RAM captures.

---

### `protocol-reverse-engineering`

Network protocol reverse engineering: packet analysis, protocol dissection, custom protocol documentation. Triggers on network traffic analysis, proprietary protocol understanding, and debugging network communication.

---

## Scope guidance

This plugin is intended for **authorized security testing, defensive security, CTF challenges, educational contexts, and legitimate research**. Refuses requests for destructive techniques, mass targeting, supply chain compromise, or detection evasion for malicious purposes. Dual-use coverage (unpacking, anti-debug, C2 analysis) requires a clear authorization context such as a penetration testing engagement, CTF competition, security research, or defensive use case.

---

## Attribution

Vendored from [`wshobson/agents/plugins/reverse-engineering`](https://github.com/wshobson/agents/tree/main/plugins/reverse-engineering) (MIT). Each agent and skill file carries an inline MIT attribution header. Tracked for ongoing sync in `CLAUDE.md`.

---

**Related:** [senior-review](senior-review.md) (security-auditor agent for source-level review) | [platform-engineering](platform-engineering.md) (cross-platform security rulebook)
