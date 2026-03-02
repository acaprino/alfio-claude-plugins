#!/usr/bin/env python3
"""
app-explorer crawler -- BFS webapp exploration with Playwright.

Usage:
    python crawler.py --url http://localhost:3000
    python crawler.py --url http://localhost:3000 --max-depth 3 --max-screens 50
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.sync_api import Browser, Page, sync_playwright


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BFS webapp explorer")
    parser.add_argument("--url", required=True, help="Starting URL")
    parser.add_argument("--output", default=".app-explorer", help="Output directory")
    parser.add_argument("--max-depth", type=int, default=5, help="Max BFS depth")
    parser.add_argument("--max-screens", type=int, default=200, help="Max screens to explore")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# URL utilities
# ---------------------------------------------------------------------------

def normalize_url(url: str, base_origin: str) -> str:
    """Return a canonical URL string for visited-set keying."""
    parsed = urlparse(url)
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc or urlparse(base_origin).netloc,
        parsed.path.rstrip("/") or "/",
        "",  # params
        "",  # query — strip all, treat same path as same state
        "",  # fragment
    ))
    # SPA hash routing: treat /#/route as a separate path
    if parsed.fragment and parsed.fragment.startswith("/"):
        normalized = normalized + "#" + parsed.fragment
    return normalized


def is_internal_url(url: str, base_origin: str) -> bool:
    """Return True if url belongs to the same origin as base_origin."""
    if not url:
        return False
    if url.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
        return False
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return False
    if parsed.netloc and parsed.netloc != urlparse(base_origin).netloc:
        return False
    return True


def resolve_url(href: str, current_url: str) -> str:
    return urljoin(current_url, href)


# ---------------------------------------------------------------------------
# DOM extraction
# ---------------------------------------------------------------------------

def scroll_to_bottom(page: Page) -> None:
    """Scroll page to reveal lazy-loaded elements."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(300)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(200)


def _best_selector(locator) -> str:
    """Return the most useful CSS/text selector for an element."""
    try:
        el_id = locator.get_attribute("id")
        if el_id:
            return f"#{el_id}"
    except Exception:
        pass
    try:
        test_id = locator.get_attribute("data-testid")
        if test_id:
            return f"[data-testid='{test_id}']"
    except Exception:
        pass
    try:
        text = locator.inner_text().strip()[:40]
        if text:
            return f"text={text}"
    except Exception:
        pass
    return ""


def extract_interactive_elements(page: Page, base_origin: str, current_url: str) -> list[dict]:
    """Extract all interactive elements from the current page."""
    elements = []

    # Buttons
    for btn in page.locator("button:visible").all():
        try:
            label = (btn.get_attribute("aria-label") or btn.inner_text()).strip()
            if label:
                elements.append({"type": "button", "label": label[:120], "selector": _best_selector(btn)})
        except Exception:
            pass

    # Internal links
    for link in page.locator("a[href]:visible").all():
        try:
            href = link.get_attribute("href") or ""
            resolved = resolve_url(href, current_url)
            if is_internal_url(resolved, base_origin):
                label = (link.get_attribute("aria-label") or link.inner_text()).strip() or href
                elements.append({"type": "link", "label": label[:120], "href": resolved})
        except Exception:
            pass

    # Dropdowns / comboboxes
    for sel in page.locator("select:visible, [role='combobox']:visible, [role='listbox']:visible").all():
        try:
            label = (sel.get_attribute("aria-label") or sel.get_attribute("name") or "dropdown").strip()
            options = []
            for opt in sel.locator("option").all():
                opt_text = opt.inner_text().strip()
                if opt_text:
                    options.append({"label": opt_text[:80]})
            if options:
                elements.append({"type": "dropdown", "label": label[:120], "options": options})
        except Exception:
            pass

    # Tabs
    for tab in page.locator("[role='tab']:visible").all():
        try:
            label = (tab.get_attribute("aria-label") or tab.inner_text()).strip()
            if label:
                elements.append({"type": "tab", "label": label[:120], "selector": _best_selector(tab)})
        except Exception:
            pass

    # Menu items
    for item in page.locator("[role='menuitem']:visible, [role='option']:visible").all():
        try:
            label = (item.get_attribute("aria-label") or item.inner_text()).strip()
            if label:
                elements.append({"type": "menu_item", "label": label[:120], "selector": _best_selector(item)})
        except Exception:
            pass

    return elements


# ---------------------------------------------------------------------------
# State fingerprinting
# ---------------------------------------------------------------------------

def compute_fingerprint(url: str, elements: list[dict], base_origin: str) -> str:
    """Unique identifier for a (url, DOM-state) pair."""
    norm_url = normalize_url(url, base_origin)
    labels = sorted(e.get("label", "") for e in elements if e.get("label"))
    dom_hash = hashlib.md5("|".join(labels).encode()).hexdigest()[:8]
    return f"{norm_url}::{dom_hash}"


# ---------------------------------------------------------------------------
# Non-href element exploration (modals, tabs, menu items)
# ---------------------------------------------------------------------------

def explore_clickable_element(
    page: Page,
    element: dict,
    current_screen_id: str,
    screen_counter: int,
    visited: set,
    base_origin: str,
    screenshots_dir: Path,
    output_dir: str,
    depth: int,
    current_path: list,
) -> dict | None:
    """
    Click a non-link element, check if it opened a new state, capture it.
    Returns a new screen dict or None if state was already visited.
    """
    selector = element.get("selector", "")
    if not selector:
        return None

    try:
        page.locator(selector).first.click(timeout=3000)
        page.wait_for_timeout(500)

        try:
            page.wait_for_load_state("networkidle", timeout=2000)
        except Exception:
            pass

        scroll_to_bottom(page)
        new_elements = extract_interactive_elements(page, base_origin, page.url)
        fp = compute_fingerprint(page.url, new_elements, base_origin)

        if fp in visited:
            return None

        visited.add(fp)
        screen_id = f"screen_{screen_counter:03d}"
        screenshot_path = str(Path(output_dir) / "screenshots" / f"{screen_id}.png")

        try:
            page.screenshot(path=screenshot_path, full_page=True, timeout=5000)
        except Exception:
            screenshot_path = ""

        new_path = current_path + [{
            "step": depth + 1,
            "from_screen": current_screen_id,
            "action": f"click:{element['type']}",
            "label": element.get("label", ""),
        }]

        screen = {
            "id": screen_id,
            "url": page.url,
            "title": page.title(),
            "screenshot": screenshot_path,
            "depth": depth + 1,
            "min_clicks_from_root": depth + 1,
            "path_from_root": new_path,
            "reached_via": {
                "from_screen": current_screen_id,
                "action": f"click:{element['type']}",
                "label": element.get("label", ""),
            },
            "elements": new_elements,
        }

        # Try to dismiss modal / restore original state
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception:
            pass

        return screen

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Post-crawl computations
# ---------------------------------------------------------------------------

def compute_meta_metrics(screens: dict) -> dict:
    if not screens:
        return {}
    clicks_list = [s["min_clicks_from_root"] for s in screens.values()]
    all_actions = sum(len(s.get("elements", [])) for s in screens.values())
    max_clicks = max(clicks_list)
    deepest = next(s for s in screens.values() if s["min_clicks_from_root"] == max_clicks)
    return {
        "total_screens": len(screens),
        "total_actions": all_actions,
        "avg_clicks_to_reach_any_screen": round(sum(clicks_list) / len(clicks_list), 2),
        "max_clicks_to_reach_any_screen": max_clicks,
        "deepest_screen": {
            "id": deepest["id"],
            "title": deepest["title"],
            "min_clicks": max_clicks,
        },
    }


def build_navigation_graph(screens: dict) -> dict:
    graph: dict[str, list[str]] = {}
    for screen_id, screen in screens.items():
        neighbors = [
            el["leads_to"]
            for el in screen.get("elements", [])
            if el.get("leads_to") and el["leads_to"] != screen_id
        ]
        if neighbors:
            graph[screen_id] = neighbors
    return graph


def build_workflows(screens: dict) -> list[dict]:
    workflows = []
    for screen_id, screen in screens.items():
        path = screen.get("path_from_root", [])
        steps = [
            {
                "step": entry["step"],
                "screen": entry["from_screen"],
                "title": screens.get(entry["from_screen"], {}).get("title", ""),
                "action": f"{entry['action']}:{entry['label']}",
            }
            for entry in path
        ]
        steps.append({
            "step": screen["depth"],
            "screen": screen_id,
            "title": screen["title"],
            "action": None,
        })
        workflows.append({
            "id": f"wf_to_{screen_id}",
            "destination_screen": screen_id,
            "destination_title": screen["title"],
            "destination_url": screen["url"],
            "min_clicks": screen["min_clicks_from_root"],
            "steps": steps,
        })
    workflows.sort(key=lambda w: w["min_clicks"])
    return workflows


# ---------------------------------------------------------------------------
# Main BFS loop
# ---------------------------------------------------------------------------

def crawl(start_url: str, output_dir: str, max_depth: int, max_screens: int) -> None:
    output_path = Path(output_dir)
    screenshots_dir = output_path / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    log_path = output_path / "crawl.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )
    log = logging.getLogger("crawler")

    parsed_start = urlparse(start_url)
    base_origin = f"{parsed_start.scheme}://{parsed_start.netloc}"

    screens: dict[str, dict] = {}
    visited: set[str] = set()
    screen_counter = 0

    queue: deque[dict] = deque([{
        "url": start_url,
        "depth": 0,
        "path": [],
        "reached_via": None,
    }])

    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        context.on("page", lambda p: p.on("dialog", lambda d: d.dismiss()))
        page: Page = context.new_page()

        # --- Login phase ---
        log.info("Navigating to %s", start_url)
        page.goto(start_url)
        page.wait_for_load_state("networkidle", timeout=15000)

        print("\n" + "=" * 60)
        print("Browser aperto. Effettua il login se necessario,")
        print("poi premi Invio per avviare il crawl...")
        print("=" * 60 + "\n")
        input()

        log.info("BFS crawl started. max_depth=%d max_screens=%d", max_depth, max_screens)
        start_time = time.time()

        # --- BFS ---
        while queue:
            if screen_counter >= max_screens:
                log.info("max_screens limit reached (%d)", max_screens)
                break

            state = queue.popleft()
            url = state["url"]
            depth = state["depth"]
            path = state["path"]

            if depth > max_depth:
                continue

            try:
                page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception as exc:
                log.warning("Navigation failed for %s: %s", url, exc)
                continue

            scroll_to_bottom(page)
            elements = extract_interactive_elements(page, base_origin, page.url)
            fp = compute_fingerprint(page.url, elements, base_origin)

            if fp in visited:
                log.debug("Skip visited state: %s", fp[:60])
                continue
            visited.add(fp)

            screen_id = f"screen_{screen_counter:03d}"
            screenshot_path = str(screenshots_dir / f"{screen_id}.png")

            try:
                page.screenshot(path=screenshot_path, full_page=True, timeout=8000)
            except Exception as exc:
                log.warning("Screenshot failed for %s: %s", url, exc)
                screenshot_path = ""

            log.info("[%d] %s  %s", screen_counter, screen_id, page.url)

            # Enqueue link children + mark leads_to as None (resolved post-crawl)
            enriched_elements = []
            for el in elements:
                enriched = dict(el)
                if el["type"] == "link":
                    enriched["leads_to"] = None
                    if depth < max_depth and screen_counter < max_screens:
                        queue.append({
                            "url": el.get("href", ""),
                            "depth": depth + 1,
                            "path": path + [{
                                "step": depth + 1,
                                "from_screen": screen_id,
                                "action": "click:link",
                                "label": el.get("label", ""),
                            }],
                            "reached_via": {
                                "from_screen": screen_id,
                                "action": "click:link",
                                "label": el.get("label", ""),
                            },
                        })
                enriched_elements.append(enriched)

            # Explore clickable non-link elements (buttons, tabs, menu items)
            if depth < max_depth:
                for el in elements:
                    if el["type"] not in ("button", "tab", "menu_item"):
                        continue
                    if screen_counter >= max_screens:
                        break
                    new_screen = explore_clickable_element(
                        page, el, screen_id,
                        screen_counter + 1,
                        visited, base_origin,
                        screenshots_dir, output_dir,
                        depth, path,
                    )
                    if new_screen:
                        screens[new_screen["id"]] = new_screen
                        screen_counter += 1
                        log.info("[%d] %s  (via click:%s)", screen_counter - 1, new_screen["id"], el.get("label", ""))

                    # Re-navigate back to current URL after each click
                    try:
                        page.goto(url, wait_until="networkidle", timeout=10000)
                        scroll_to_bottom(page)
                    except Exception:
                        break

            screens[screen_id] = {
                "id": screen_id,
                "url": page.url,
                "title": page.title(),
                "screenshot": screenshot_path,
                "depth": depth,
                "min_clicks_from_root": depth,
                "path_from_root": path,
                "reached_via": state["reached_via"],
                "elements": enriched_elements,
            }
            screen_counter += 1

        browser.close()

    # --- Post-crawl: resolve leads_to for link elements ---
    url_to_screen: dict[str, str] = {
        normalize_url(s["url"], base_origin): sid
        for sid, s in screens.items()
    }
    for screen in screens.values():
        for el in screen.get("elements", []):
            if el["type"] == "link" and el.get("href"):
                el["leads_to"] = url_to_screen.get(normalize_url(el["href"], base_origin))

    # --- Build sitemap ---
    metrics = compute_meta_metrics(screens)
    elapsed = round(time.time() - start_time, 1)

    sitemap = {
        "meta": {
            "app_url": start_url,
            "explored_at": datetime.now(timezone.utc).isoformat(),
            "crawl_duration_seconds": elapsed,
            **metrics,
        },
        "screens": screens,
        "navigation_graph": build_navigation_graph(screens),
        "workflows": build_workflows(screens),
    }

    sitemap_path = output_path / "sitemap.json"
    with sitemap_path.open("w", encoding="utf-8") as f:
        json.dump(sitemap, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Crawl completato in {elapsed}s")
    print(f"  Schermate trovate:   {metrics.get('total_screens', 0)}")
    print(f"  Azioni totali:       {metrics.get('total_actions', 0)}")
    print(f"  Click max (worst):   {metrics.get('max_clicks_to_reach_any_screen', 0)}")
    print(f"  Click medi:          {metrics.get('avg_clicks_to_reach_any_screen', 0)}")
    print(f"  Schermata piu deep:  {metrics.get('deepest_screen', {}).get('title', '')} "
          f"({metrics.get('deepest_screen', {}).get('min_clicks', 0)} click)")
    print(f"\nOutput: {sitemap_path}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()
    crawl(
        start_url=args.url,
        output_dir=args.output,
        max_depth=args.max_depth,
        max_screens=args.max_screens,
    )
