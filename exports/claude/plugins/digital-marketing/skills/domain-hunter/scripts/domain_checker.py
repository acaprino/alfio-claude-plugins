#!/usr/bin/env python3
"""
Domain availability checker for the brand naming workflow.

Usage:
    python domain_checker.py name1 name2 name3
    python domain_checker.py acme --tlds .com,.io

Queries the public RDAP bootstrap service at rdap.org. No API key, no
third-party packages. A name that already contains a dot is checked as a full
domain and the --tlds list is not applied to it.

Status mapping:
    HTTP 404 -> AVAILABLE (registry holds no record)
    HTTP 200 -> TAKEN
    anything else (timeout, 429, network failure) -> UNKNOWN

UNKNOWN never means available. A TLD with no RDAP service also answers 404, so
confirm anything surprising at a registrar before buying.
"""

import argparse
import sys
import time
import urllib.error
import urllib.request

RDAP_URL = "https://rdap.org/domain/{domain}"
DEFAULT_TLDS = ".com,.app,.io,.co"
TIMEOUT = 10
DELAY = 0.5


def parse_tlds(raw: str) -> list:
    """Split a comma-separated TLD string, tolerating a missing leading dot."""
    tlds = []
    for item in raw.split(","):
        item = item.strip().lower()
        if item:
            tlds.append(item if item.startswith(".") else "." + item)
    return tlds


def build_domains(names: list, tlds: list) -> list:
    """Expand names against TLDs. Names that already carry a dot pass through."""
    domains = []
    for name in names:
        name = name.strip().lower()
        if "." in name:
            domains.append(name)
        else:
            domains.extend(name + tld for tld in tlds)
    return domains


def check_domain(domain: str) -> str:
    """Return AVAILABLE, TAKEN, or UNKNOWN for one fully qualified domain."""
    request = urllib.request.Request(
        RDAP_URL.format(domain=domain),
        headers={
            "Accept": "application/rdap+json",
            "User-Agent": "domain-checker/2.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return "TAKEN" if response.getcode() == 200 else "UNKNOWN"
    except urllib.error.HTTPError as err:
        return "AVAILABLE" if err.code == 404 else "UNKNOWN"
    except (urllib.error.URLError, OSError):
        return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(
        description="Check domain availability via RDAP (no API key needed)."
    )
    parser.add_argument(
        "names",
        nargs="+",
        help="brand names, or full domains if they contain a dot",
    )
    parser.add_argument(
        "--tlds",
        default=DEFAULT_TLDS,
        help="comma-separated TLDs to check (default: %(default)s)",
    )
    args = parser.parse_args()

    tlds = parse_tlds(args.tlds)
    if not tlds:
        parser.error("--tlds needs at least one TLD")

    domains = build_domains(args.names, tlds)
    counts = {"AVAILABLE": 0, "TAKEN": 0, "UNKNOWN": 0}

    for index, domain in enumerate(domains):
        if index:
            time.sleep(DELAY)
        status = check_domain(domain)
        counts[status] += 1
        print("{}  {}".format(domain, status))

    print()
    print("{} checked: {} available, {} taken, {} unknown".format(
        len(domains), counts["AVAILABLE"], counts["TAKEN"], counts["UNKNOWN"]
    ))
    if counts["UNKNOWN"]:
        print("UNKNOWN means the lookup failed, not that the domain is free. "
              "Retry or verify at a registrar.")

    sys.exit(2 if counts["UNKNOWN"] == len(domains) else 0)


if __name__ == "__main__":
    main()
