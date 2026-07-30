#!/usr/bin/env python3
"""
Domain availability checker for brand naming workflow.

Usage:
    python domain_checker.py name1 name2 name3

Setup:
    1. Install requests: pip install requests
    2. Set your API key as environment variable:
       export WHOIS_API_KEY="your_apilayer_whois_api_key"

    Get a free API key at: https://apilayer.com/marketplace/whois-api

Without an API key, the script will report that manual checking is needed.
"""

import os
import sys

try:
    import requests
except ImportError:
    print("Error: 'requests' package not installed. Run: pip install requests")
    sys.exit(1)

API_KEY = os.environ.get("WHOIS_API_KEY", "")
TLDS = [".com", ".app", ".io", ".co"]


def check_domain_whois(name: str, tld: str) -> str:
    """Check domain availability via APILayer WHOIS API."""
    domain = f"{name}{tld}"
    url = f"https://api.apilayer.com/whois/query?domain={domain}"
    headers = {"apikey": API_KEY}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()

        if "message" in data:
            return f"API error: {data['message']}"

        availability = (
            data.get("WhoisRecord", {})
            .get("domainAvailability", "UNKNOWN")
        )
        return availability
    except requests.RequestException as e:
        return f"Connection error: {e}"
    except ValueError:
        return "Invalid API response"


def main():
    if len(sys.argv) < 2:
        print("Usage: python domain_checker.py name1 name2 name3")
        sys.exit(1)

    names = sys.argv[1:]

    if not API_KEY:
        print("WARNING: WHOIS_API_KEY not set.")
        print("Set it with: export WHOIS_API_KEY='your_key'")
        print("Get a free key at: https://apilayer.com/marketplace/whois-api")
        print()
        print("Listing domains to check manually:")
        for name in names:
            for tld in TLDS:
                print(f"  {name}{tld}")
        sys.exit(0)

    print("--- DOMAIN AVAILABILITY CHECK ---")
    print(f"{'Name':<20} {'TLD':<8} {'Status'}")
    print("-" * 50)

    for name in names:
        for tld in TLDS:
            status = check_domain_whois(name, tld)
            print(f"{name:<20} {tld:<8} {status}")
        print()


if __name__ == "__main__":
    main()
