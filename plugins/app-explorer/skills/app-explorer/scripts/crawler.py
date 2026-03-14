#!/usr/bin/env python3
"""
app-explorer crawler -- BFS webapp exploration with Playwright.

Usage:
    python crawler.py --url http://localhost:3000
    python crawler.py --url http://localhost:3000 --max-depth 3 --max-screens 50
    python crawler.py --url http://localhost:3000 --mobile --auth auth.json
    python crawler.py --url http://localhost:3000 --no-thorough
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


# ---------------------------------------------------------------------------
# Shared selector constants (used in detect_overlay, extract_overlay_elements,
# compute_fingerprint, and _dismiss_overlay to avoid duplication)
# ---------------------------------------------------------------------------

DIALOG_SELECTORS_JS = (
    '[role="dialog"]:not([aria-hidden="true"]), '
    '[role="alertdialog"]:not([aria-hidden="true"]), '
    'dialog[open]'
)

MODAL_SELECTORS_JS = [
    '.modal.show', '.modal.active', '.modal[open]',
    '[class*="Modal"][class*="open"]',
    '[class*="Modal"][class*="visible"]',
    '[class*="modal"][class*="show"]',
    '.overlay:not([aria-hidden="true"])',
    '[class*="Overlay"]:not([aria-hidden="true"])',
]

DRAWER_SELECTORS_JS = [
    '[class*="drawer"][class*="open"]',
    '[class*="Drawer"][class*="open"]',
    '[class*="sidebar"][class*="open"]',
    '[class*="Sidebar"][class*="open"]',
    '[class*="drawer"][class*="visible"]',
    '[class*="Drawer"][class*="visible"]',
    '[class*="bottom-sheet"][class*="open"]',
    '[class*="BottomSheet"][class*="open"]',
]

# All overlay selectors combined for container detection
ALL_OVERLAY_SELECTORS_JS = (
    [DIALOG_SELECTORS_JS.replace(", ", "', '")]
    + MODAL_SELECTORS_JS
    + DRAWER_SELECTORS_JS
)

# Cap for cursor:pointer scanning in detect_all_clickables
MAX_CURSOR_POINTER_SCAN = 500


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BFS webapp explorer")
    parser.add_argument("--url", required=True, help="Starting URL")
    parser.add_argument("--output", default=".app-explorer", help="Output directory")
    parser.add_argument("--max-depth", type=int, default=5, help="Max BFS depth")
    parser.add_argument("--max-screens", type=int, default=200, help="Max screens to explore")
    parser.add_argument("--mobile", action=argparse.BooleanOptionalAction,
                        default=True, help="Use mobile viewport (default: True)")
    parser.add_argument("--width", type=int, default=390,
                        help="Viewport width (default: 390)")
    parser.add_argument("--height", type=int, default=844,
                        help="Viewport height (default: 844)")
    parser.add_argument("--auth", default=None,
                        help="Path to auth.json from a previous crawl to skip login")
    parser.add_argument("--thorough", action=argparse.BooleanOptionalAction,
                        default=True,
                        help="Enable exhaustive element detection (default: True)")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Crawl context (shared mutable state to avoid threading 15+ params)
# ---------------------------------------------------------------------------

@dataclass
class CrawlContext:
    """Shared state for the crawl session."""
    base_origin: str
    output_dir: str
    screenshots_dir: Path
    visited: set = field(default_factory=set)
    thorough: bool = True
    max_overlay_depth: int = 3
    log: logging.Logger = field(default_factory=lambda: logging.getLogger("crawler"))
    screen_counter: int = 0

    def next_screen_id(self) -> str:
        """Mint a new screen_id and increment the counter atomically."""
        sid = f"screen_{self.screen_counter:03d}"
        self.screen_counter += 1
        return sid


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
        "",  # query - strip all, treat same path as same state
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
# Selector sanitization
# ---------------------------------------------------------------------------

_SELECTOR_UNSAFE_RE = re.compile(r"['\"\\\[\](){}|]")


def _sanitize_selector_value(value: str) -> str:
    """Remove characters that could break CSS selector interpolation."""
    return _SELECTOR_UNSAFE_RE.sub("", value).strip()


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
            safe_id = _sanitize_selector_value(el_id)
            if safe_id:
                return f"#{safe_id}"
    except Exception:
        pass
    try:
        test_id = locator.get_attribute("data-testid")
        if test_id:
            safe_tid = _sanitize_selector_value(test_id)
            if safe_tid:
                return f"[data-testid='{safe_tid}']"
    except Exception:
        pass
    try:
        text = locator.inner_text().strip()[:40]
        if text:
            return f"text={text}"
    except Exception:
        pass
    return ""


def _safe_label(locator, fallback: str = "") -> str:
    """Extract a label from an element using multiple strategies."""
    try:
        aria = locator.get_attribute("aria-label")
        if aria and aria.strip():
            return aria.strip()[:120]
    except Exception:
        pass
    try:
        title = locator.get_attribute("title")
        if title and title.strip():
            return title.strip()[:120]
    except Exception:
        pass
    try:
        placeholder = locator.get_attribute("placeholder")
        if placeholder and placeholder.strip():
            return placeholder.strip()[:120]
    except Exception:
        pass
    try:
        name = locator.get_attribute("name")
        if name and name.strip():
            return name.strip()[:120]
    except Exception:
        pass
    try:
        text = locator.inner_text().strip()
        if text:
            return text[:120]
    except Exception:
        pass
    return fallback[:120] if fallback else ""


def _has_only_icon(locator) -> bool:
    """Check if a button/element contains only an icon (SVG/img) with no text."""
    try:
        text = locator.inner_text().strip()
        if text:
            return False
        has_icon = locator.evaluate(
            "el => el.querySelector('svg, img, i[class*=\"icon\"], span[class*=\"icon\"]') !== null"
        )
        return bool(has_icon)
    except Exception:
        return False


def extract_interactive_elements(
    page: Page,
    base_origin: str,
    current_url: str,
    *,
    thorough: bool = True,
) -> list[dict]:
    """Extract all interactive elements from the current page.

    When thorough=True, detects an exhaustive set of element types beyond
    the basic buttons, links, dropdowns, tabs, menu_items, and nav_items.
    """
    elements: list[dict] = []
    seen_labels: set[str] = set()

    def _add(el_type: str, label: str, extra: dict | None = None) -> None:
        """Deduplicate by (type, label) before appending."""
        key = f"{el_type}::{label}"
        if key in seen_labels or not label:
            return
        seen_labels.add(key)
        entry: dict = {"type": el_type, "label": label}
        if extra:
            entry.update(extra)
        elements.append(entry)

    # ------------------------------------------------------------------
    # Core element types (always active)
    # ------------------------------------------------------------------

    # Buttons
    for btn in page.locator("button:visible").all():
        try:
            label = (btn.get_attribute("aria-label") or btn.inner_text()).strip()
            if label:
                el_type = "button"
                if thorough and _has_only_icon(btn):
                    el_type = "icon_button"
                _add(el_type, label[:120], {"selector": _best_selector(btn)})
        except Exception:
            pass

    # Internal links
    for link in page.locator("a[href]:visible").all():
        try:
            href = link.get_attribute("href") or ""
            resolved = resolve_url(href, current_url)
            if is_internal_url(resolved, base_origin):
                label = (link.get_attribute("aria-label") or link.inner_text()).strip() or href
                _add("link", label[:120], {"href": resolved})
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
                _add("dropdown", label[:120], {"options": options})
        except Exception:
            pass

    # Tabs
    for tab in page.locator("[role='tab']:visible").all():
        try:
            label = (tab.get_attribute("aria-label") or tab.inner_text()).strip()
            if label:
                _add("tab", label[:120], {"selector": _best_selector(tab)})
        except Exception:
            pass

    # Menu items
    for item in page.locator("[role='menuitem']:visible, [role='option']:visible").all():
        try:
            label = (item.get_attribute("aria-label") or item.inner_text()).strip()
            if label:
                _add("menu_item", label[:120], {"selector": _best_selector(item)})
        except Exception:
            pass

    # Bottom nav items (common SPA pattern)
    for nav_item in page.locator(
        "nav button, nav [role='button'], "
        "[class*='bottom-nav'] button, [class*='BottomNav'] button, "
        "[class*='tab-bar'] button, [class*='TabBar'] button"
    ).all():
        try:
            label = (nav_item.get_attribute("aria-label") or nav_item.inner_text()).strip()
            if label and len(label) < 30:
                _add("nav_item", label[:120], {"selector": _best_selector(nav_item)})
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Extended element types (thorough mode only)
    # ------------------------------------------------------------------
    if not thorough:
        return elements

    _extract_extended_elements(page, base_origin, current_url, _add)

    return elements


def _extract_extended_elements(
    page: Page,
    base_origin: str,
    current_url: str,
    _add,
) -> None:
    """Extract thorough-mode element types (called from extract_interactive_elements)."""

    # --- Form fields: text inputs ---
    for inp in page.locator(
        "input[type='text']:visible, input[type='email']:visible, "
        "input[type='password']:visible, input[type='number']:visible, "
        "input[type='tel']:visible, input[type='url']:visible, "
        "input:not([type]):visible"
    ).all():
        try:
            label = _safe_label(inp, "text_input")
            inp_type = inp.get_attribute("type") or "text"
            _add("form_field", label, {"selector": _best_selector(inp), "input_type": inp_type})
        except Exception:
            pass

    # --- Form fields: textarea ---
    for ta in page.locator("textarea:visible").all():
        try:
            label = _safe_label(ta, "textarea")
            _add("form_field", label, {"selector": _best_selector(ta), "input_type": "textarea"})
        except Exception:
            pass

    # --- File upload inputs ---
    for fu in page.locator("input[type='file']").all():
        try:
            label = _safe_label(fu, "file_upload")
            _add("file_upload", label, {"selector": _best_selector(fu)})
        except Exception:
            pass

    # --- Search inputs ---
    for si in page.locator("input[type='search']:visible, [role='searchbox']:visible").all():
        try:
            label = _safe_label(si, "search")
            _add("search_input", label, {"selector": _best_selector(si)})
        except Exception:
            pass

    # --- Date/time pickers ---
    for dp in page.locator(
        "input[type='date']:visible, input[type='time']:visible, "
        "input[type='datetime-local']:visible, input[type='month']:visible, "
        "input[type='week']:visible"
    ).all():
        try:
            label = _safe_label(dp, "date_picker")
            inp_type = dp.get_attribute("type") or "date"
            _add("date_picker", label, {"selector": _best_selector(dp), "input_type": inp_type})
        except Exception:
            pass

    # --- Color picker ---
    for cp in page.locator("input[type='color']:visible").all():
        try:
            label = _safe_label(cp, "color_picker")
            _add("color_picker", label, {"selector": _best_selector(cp)})
        except Exception:
            pass

    # --- Checkboxes ---
    for cb in page.locator("input[type='checkbox']:visible, [role='checkbox']:visible").all():
        try:
            label = _safe_label(cb, "checkbox")
            is_toggle = False
            try:
                is_toggle = cb.evaluate("""el => {
                    const parent = el.parentElement;
                    if (!parent) return false;
                    const cls = (parent.className || '') + ' ' + (el.className || '');
                    return /toggle|switch/i.test(cls);
                }""")
            except Exception:
                pass
            el_type = "toggle" if is_toggle else "checkbox"
            _add(el_type, label, {"selector": _best_selector(cb)})
        except Exception:
            pass

    # --- Toggles/switches (role-based) ---
    for sw in page.locator("[role='switch']:visible").all():
        try:
            label = _safe_label(sw, "toggle")
            _add("toggle", label, {"selector": _best_selector(sw)})
        except Exception:
            pass

    # --- CSS class-based toggles ---
    for tg in page.locator(".toggle:visible, .switch:visible").all():
        try:
            label = _safe_label(tg, "toggle")
            _add("toggle", label, {"selector": _best_selector(tg)})
        except Exception:
            pass

    # --- Radio buttons ---
    for rb in page.locator(
        "input[type='radio']:visible, [role='radio']:visible"
    ).all():
        try:
            label = _safe_label(rb, "radio")
            _add("radio", label, {"selector": _best_selector(rb)})
        except Exception:
            pass

    # --- Radio groups ---
    for rg in page.locator("[role='radiogroup']:visible").all():
        try:
            label = _safe_label(rg, "radio_group")
            _add("radio_group", label, {"selector": _best_selector(rg)})
        except Exception:
            pass

    # --- Sliders ---
    for sl in page.locator("input[type='range']:visible, [role='slider']:visible").all():
        try:
            label = _safe_label(sl, "slider")
            _add("slider", label, {"selector": _best_selector(sl)})
        except Exception:
            pass

    # --- Accordions/expandables (only semantic accordions, not generic aria-expanded) ---
    for acc in page.locator(
        "details > summary:visible, "
        ".accordion:visible, [data-accordion]:visible"
    ).all():
        try:
            label = _safe_label(acc, "accordion")
            expanded = acc.get_attribute("aria-expanded")
            extra: dict = {"selector": _best_selector(acc)}
            if expanded is not None:
                extra["expanded"] = expanded == "true"
            _add("accordion", label, extra)
        except Exception:
            pass

    # --- Expandable buttons (aria-expanded but not accordion) ---
    for exp in page.locator("[role='button'][aria-expanded]:visible").all():
        try:
            label = _safe_label(exp, "expandable")
            expanded = exp.get_attribute("aria-expanded")
            extra = {"selector": _best_selector(exp), "expanded": expanded == "true"}
            _add("expandable", label, extra)
        except Exception:
            pass

    # --- Chips/tags ---
    for chip in page.locator(
        ".chip:visible, .tag:visible, .badge:visible, "
        "[class*='Chip']:visible, [class*='Tag']:visible"
    ).all():
        try:
            label = _safe_label(chip, "chip")
            _add("chip", label, {"selector": _best_selector(chip)})
        except Exception:
            pass

    # --- Tooltip/popover triggers ---
    for tt in page.locator(
        "[data-tooltip]:visible, [data-popover]:visible, "
        "[aria-describedby]:visible"
    ).all():
        try:
            label = _safe_label(tt, "tooltip_trigger")
            if label and label != "tooltip_trigger":
                _add("tooltip_trigger", label, {"selector": _best_selector(tt)})
        except Exception:
            pass

    # --- Hamburger/drawer menu buttons ---
    for hb in page.locator(
        "[aria-label*='menu' i]:visible, [aria-label*='Menu' i]:visible, "
        ".hamburger:visible, .menu-toggle:visible, "
        "[class*='hamburger']:visible, [class*='MenuToggle']:visible, "
        "[class*='menu-btn']:visible, [class*='sidebar-toggle']:visible"
    ).all():
        try:
            label = _safe_label(hb, "hamburger_menu")
            _add("drawer_trigger", label, {"selector": _best_selector(hb)})
        except Exception:
            pass

    # --- Context menu triggers ---
    for cm in page.locator(
        "[aria-haspopup='true']:visible, [aria-haspopup='menu']:visible"
    ).all():
        try:
            label = _safe_label(cm, "context_menu_trigger")
            _add("context_menu_trigger", label, {"selector": _best_selector(cm)})
        except Exception:
            pass

    # --- Dialog triggers ---
    for dt in page.locator("[aria-haspopup='dialog']:visible").all():
        try:
            label = _safe_label(dt, "dialog_trigger")
            _add("dialog_trigger", label, {"selector": _best_selector(dt)})
        except Exception:
            pass

    # --- Toolbar buttons ---
    for tb in page.locator("[role='toolbar'] button:visible").all():
        try:
            label = _safe_label(tb, "toolbar_button")
            _add("toolbar_button", label, {"selector": _best_selector(tb)})
        except Exception:
            pass

    # --- Tree items ---
    for ti in page.locator("[role='treeitem']:visible").all():
        try:
            label = _safe_label(ti, "tree_item")
            _add("tree_item", label, {"selector": _best_selector(ti)})
        except Exception:
            pass

    # --- Steppers/pagination ---
    for sp in page.locator(
        ".stepper:visible, .pagination:visible, "
        "[class*='Stepper']:visible, [class*='Pagination']:visible, "
        "[role='navigation'] a:visible"
    ).all():
        try:
            label = _safe_label(sp, "pagination")
            _add("pagination", label, {"selector": _best_selector(sp)})
        except Exception:
            pass

    # --- Snackbar/toast dismiss buttons ---
    for sb in page.locator(
        ".snackbar button:visible, .toast button:visible, "
        "[class*='Snackbar'] button:visible, [class*='Toast'] button:visible, "
        "[role='alert'] button:visible"
    ).all():
        try:
            label = _safe_label(sb, "dismiss")
            _add("snackbar_action", label, {"selector": _best_selector(sb)})
        except Exception:
            pass

    # --- Clickable cards ---
    for card in page.locator(
        ".card[onclick]:visible, [role='article'] a:visible, "
        "[role='listitem']:visible, [class*='Card']:visible"
    ).all():
        try:
            is_clickable = card.evaluate("""el => {
                return el.hasAttribute('onclick') ||
                    el.tagName === 'A' ||
                    el.querySelector('a') !== null ||
                    getComputedStyle(el).cursor === 'pointer';
            }""")
            if is_clickable:
                label = _safe_label(card, "card")
                _add("card_action", label, {"selector": _best_selector(card)})
        except Exception:
            pass

    # --- FABs (floating action buttons) ---
    for fab in page.locator(
        "[class*='fab']:visible, [class*='Fab']:visible, "
        "[class*='floating-action']:visible, [class*='FloatingAction']:visible"
    ).all():
        try:
            label = _safe_label(fab, "fab")
            _add("fab", label, {"selector": _best_selector(fab)})
        except Exception:
            pass


# ---------------------------------------------------------------------------
# JavaScript-based exhaustive clickable detection
# ---------------------------------------------------------------------------

def detect_all_clickables(page: Page) -> list[dict]:
    """Use JavaScript to find ALL clickable elements on the page.

    This catches custom components that don't use standard HTML elements.
    Returns a list of dicts with type, label, and selector.
    """
    try:
        raw = page.evaluate("""(maxScan) => {
            const results = [];
            const seen = new Set();

            function getLabel(el) {
                return (
                    el.getAttribute('aria-label') ||
                    el.getAttribute('title') ||
                    el.getAttribute('alt') ||
                    el.textContent?.trim().substring(0, 120) ||
                    ''
                );
            }

            function getSelector(el) {
                if (el.id) return '#' + CSS.escape(el.id);
                const testId = el.getAttribute('data-testid');
                if (testId) return "[data-testid='" + CSS.escape(testId) + "']";
                return '';
            }

            function isVisible(el) {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) return false;
                const style = getComputedStyle(el);
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       style.opacity !== '0';
            }

            function addEl(el, type) {
                if (!isVisible(el)) return;
                const label = getLabel(el);
                const key = type + '::' + label;
                if (seen.has(key) || !label) return;
                seen.add(key);
                results.push({
                    type: type,
                    label: label.substring(0, 120),
                    selector: getSelector(el)
                });
            }

            // Elements with onclick attribute
            document.querySelectorAll('[onclick]').forEach(el => {
                addEl(el, 'generic_clickable');
            });

            // Elements with cursor: pointer computed style
            // (capped to avoid scanning entire DOM on large pages)
            const allEls = document.querySelectorAll(
                'div, span, li, article, section, header, footer, aside, main, p, label, figure, figcaption'
            );
            for (let i = 0; i < allEls.length && i < maxScan; i++) {
                const el = allEls[i];
                try {
                    const style = getComputedStyle(el);
                    if (style.cursor === 'pointer') {
                        const tag = el.tagName.toLowerCase();
                        if (['button', 'a', 'input', 'select', 'textarea'].includes(tag)) continue;
                        if (el.getAttribute('role')) continue;
                        addEl(el, 'generic_clickable');
                    }
                } catch(e) {}
            }

            // Role-based clickables not yet captured
            document.querySelectorAll(
                '[role="button"], [role="link"], [role="menuitem"], ' +
                '[role="tab"], [role="option"], [role="treeitem"]'
            ).forEach(el => {
                const tag = el.tagName.toLowerCase();
                if (['button', 'a', 'input'].includes(tag)) return;
                addEl(el, 'role_' + el.getAttribute('role'));
            });

            // Elements with tabindex that are interactive
            document.querySelectorAll('[tabindex]').forEach(el => {
                const idx = parseInt(el.getAttribute('tabindex'), 10);
                if (idx < 0) return;
                const tag = el.tagName.toLowerCase();
                if (['button', 'a', 'input', 'select', 'textarea'].includes(tag)) return;
                if (el.getAttribute('role')) return;
                addEl(el, 'focusable_interactive');
            });

            // Elements with aria-haspopup
            document.querySelectorAll('[aria-haspopup]').forEach(el => {
                const popup = el.getAttribute('aria-haspopup');
                addEl(el, 'popup_trigger_' + popup);
            });

            return results;
        }""", MAX_CURSOR_POINTER_SCAN)
        return raw if isinstance(raw, list) else []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Hamburger/drawer menu exploration
# ---------------------------------------------------------------------------

HAMBURGER_SELECTORS = [
    "[aria-label*='menu' i]",
    "[aria-label*='navigation' i]",
    ".hamburger",
    ".menu-toggle",
    "[class*='hamburger']",
    "[class*='MenuToggle']",
    "[class*='menu-btn']",
    "[class*='sidebar-toggle']",
    "[class*='drawer-toggle']",
]

DRAWER_CONTAINER_SELECTORS = [
    "[role='navigation']:visible",
    "[class*='drawer']:visible",
    "[class*='Drawer']:visible",
    "[class*='sidebar']:visible",
    "[class*='Sidebar']:visible",
    "[class*='side-menu']:visible",
    "nav:visible",
]


def explore_hamburger_menu(
    page: Page,
    base_origin: str,
    current_url: str,
    thorough: bool,
    log: logging.Logger,
    ctx: CrawlContext | None = None,
) -> tuple[list[dict], dict | None]:
    """Try to find and open hamburger/drawer menus, extract their items.

    Returns (drawer_elements, drawer_screen) where drawer_screen is a screen
    dict with a screenshot of the open drawer state (or None).
    """
    drawer_elements: list[dict] = []
    drawer_screen: dict | None = None
    seen: set[str] = set()

    def _add_drawer(el_type: str, label: str, extra: dict | None = None) -> None:
        key = f"{el_type}::{label}"
        if key in seen or not label:
            return
        seen.add(key)
        entry: dict = {"type": el_type, "label": label}
        if extra:
            entry.update(extra)
        drawer_elements.append(entry)

    for selector in HAMBURGER_SELECTORS:
        try:
            btn = page.locator(f"{selector}:visible").first
            if not btn.is_visible(timeout=500):
                continue

            btn.click(timeout=2000)
            page.wait_for_timeout(600)

            for ds in DRAWER_CONTAINER_SELECTORS:
                try:
                    drawer = page.locator(ds).first
                    if not drawer.is_visible(timeout=300):
                        continue
                    for link in drawer.locator("a[href]:visible").all():
                        try:
                            href = link.get_attribute("href") or ""
                            resolved = resolve_url(href, current_url)
                            if is_internal_url(resolved, base_origin):
                                label = _safe_label(link, href)
                                _add_drawer("drawer_item", label[:120], {
                                    "href": resolved,
                                    "selector": _best_selector(link),
                                })
                        except Exception:
                            pass

                    for item in drawer.locator("button:visible, [role='menuitem']:visible").all():
                        try:
                            label = _safe_label(item, "")
                            _add_drawer("drawer_item", label[:120], {
                                "selector": _best_selector(item),
                            })
                        except Exception:
                            pass
                except Exception:
                    pass

            # Screenshot the open drawer state before closing
            if drawer_elements and ctx is not None:
                try:
                    drawer_sid = ctx.next_screen_id()
                    drawer_ss_path = str(ctx.screenshots_dir / f"{drawer_sid}.png")
                    page.screenshot(path=drawer_ss_path, full_page=False, timeout=5000)
                    drawer_screen = {
                        "id": drawer_sid,
                        "url": page.url,
                        "title": f"Drawer menu - {page.title()}",
                        "screenshot": drawer_ss_path,
                        "depth": 0,
                        "min_clicks_from_root": 1,
                        "path_from_root": [],
                        "reached_via": {"from_screen": None, "action": "open_drawer", "label": "hamburger_menu"},
                        "elements": list(drawer_elements),
                        "overlay": {"type": "drawer", "title": "Navigation drawer", "visible": True},
                    }
                    if thorough:
                        drawer_screen["element_summary"] = compute_element_summary(drawer_elements)
                except Exception:
                    pass

            # Close the drawer
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
            except Exception:
                pass
            try:
                page.mouse.click(10, 10)
                page.wait_for_timeout(300)
            except Exception:
                pass

            if drawer_elements:
                log.info("  Drawer menu found: %d items extracted", len(drawer_elements))
                break

        except Exception:
            pass

    return drawer_elements, drawer_screen


# ---------------------------------------------------------------------------
# Overlay detection helpers (use shared selector constants)
# ---------------------------------------------------------------------------

def _build_overlay_detect_js() -> str:
    """Build the JS for detect_overlay using shared selector constants."""
    dialog_sel = DIALOG_SELECTORS_JS
    modal_sels = json.dumps(MODAL_SELECTORS_JS)
    drawer_sels = json.dumps(DRAWER_SELECTORS_JS)
    return f"""() => {{
        // Check for role-based overlays
        const dialog = document.querySelector('{dialog_sel}');
        if (dialog) {{
            const style = getComputedStyle(dialog);
            if (style.display !== 'none' && style.visibility !== 'hidden') {{
                const heading = dialog.querySelector('h1,h2,h3,h4,[role="heading"]');
                return {{
                    type: dialog.getAttribute('role') || 'dialog',
                    title: heading?.textContent?.trim() || dialog.getAttribute('aria-label') || '',
                    visible: true
                }};
            }}
        }}

        // Check for common modal classes
        const modalSelectors = {modal_sels};
        for (const sel of modalSelectors) {{
            const el = document.querySelector(sel);
            if (el) {{
                const style = getComputedStyle(el);
                if (style.display !== 'none' && style.visibility !== 'hidden') {{
                    const heading = el.querySelector('h1,h2,h3,h4,[role="heading"]');
                    return {{
                        type: 'modal',
                        title: heading?.textContent?.trim() || el.getAttribute('aria-label') || '',
                        visible: true
                    }};
                }}
            }}
        }}

        // Check for drawers/sidebars
        const drawerSelectors = {drawer_sels};
        for (const sel of drawerSelectors) {{
            const el = document.querySelector(sel);
            if (el) {{
                const style = getComputedStyle(el);
                if (style.display !== 'none' && style.visibility !== 'hidden') {{
                    const heading = el.querySelector('h1,h2,h3,h4,[role="heading"]');
                    const type = /bottom.?sheet/i.test(el.className) ? 'bottom_sheet' :
                                 /sidebar/i.test(el.className) ? 'sidebar' : 'drawer';
                    return {{
                        type: type,
                        title: heading?.textContent?.trim() || '',
                        visible: true
                    }};
                }}
            }}
        }}

        return null;
    }}"""


_OVERLAY_DETECT_JS = _build_overlay_detect_js()


def detect_overlay(page: Page) -> dict | None:
    """Detect if a modal/dialog/drawer/popover is currently visible."""
    try:
        return page.evaluate(_OVERLAY_DETECT_JS)
    except Exception:
        return None


def _is_overlay_visible(page: Page) -> bool:
    """Lightweight check: is ANY overlay currently visible? (no full extraction)"""
    try:
        return bool(detect_overlay(page))
    except Exception:
        return False


def _build_overlay_container_js() -> str:
    """Build JS to find the overlay container element."""
    all_sels = json.dumps(
        [DIALOG_SELECTORS_JS]
        + MODAL_SELECTORS_JS
        + DRAWER_SELECTORS_JS
    )
    return f"""() => {{
        const selectors = {all_sels};
        for (const sel of selectors) {{
            try {{
                const el = document.querySelector(sel);
                if (el) {{
                    const style = getComputedStyle(el);
                    if (style.display !== 'none' && style.visibility !== 'hidden') {{
                        if (el.id) return '#' + CSS.escape(el.id);
                        el.setAttribute('data-crawler-overlay', 'true');
                        return '[data-crawler-overlay="true"]';
                    }}
                }}
            }} catch(e) {{}}
        }}
        return null;
    }}"""


_OVERLAY_CONTAINER_JS = _build_overlay_container_js()

_OVERLAY_CLEANUP_JS = """() => {
    const el = document.querySelector('[data-crawler-overlay="true"]');
    if (el) el.removeAttribute('data-crawler-overlay');
}"""


def extract_overlay_elements(
    page: Page,
    base_origin: str,
    current_url: str,
    thorough: bool,
) -> list[dict]:
    """Extract interactive elements INSIDE an open overlay/modal/dialog."""
    try:
        container = page.evaluate(_OVERLAY_CONTAINER_JS)
        if not container:
            return []

        overlay_elements: list[dict] = []
        seen: set[str] = set()
        container_loc = page.locator(container)

        try:
            for btn in container_loc.locator("button:visible").all():
                try:
                    label = _safe_label(btn, "")
                    key = f"button::{label}"
                    if label and key not in seen:
                        seen.add(key)
                        overlay_elements.append({
                            "type": "button",
                            "label": label,
                            "selector": _best_selector(btn),
                            "in_overlay": True,
                        })
                except Exception:
                    pass

            for link in container_loc.locator("a[href]:visible").all():
                try:
                    href = link.get_attribute("href") or ""
                    resolved = resolve_url(href, current_url)
                    if is_internal_url(resolved, base_origin):
                        label = _safe_label(link, href)
                        key = f"link::{label}"
                        if label and key not in seen:
                            seen.add(key)
                            overlay_elements.append({
                                "type": "link",
                                "label": label,
                                "href": resolved,
                                "in_overlay": True,
                            })
                except Exception:
                    pass

            for inp in container_loc.locator(
                "input:visible, textarea:visible, select:visible"
            ).all():
                try:
                    label = _safe_label(inp, "input")
                    inp_type = inp.get_attribute("type") or "text"
                    tag = inp.evaluate("el => el.tagName.toLowerCase()")
                    if tag == "select":
                        inp_type = "select"
                    elif tag == "textarea":
                        inp_type = "textarea"
                    key = f"form_field::{label}"
                    if key not in seen:
                        seen.add(key)
                        overlay_elements.append({
                            "type": "form_field",
                            "label": label,
                            "input_type": inp_type,
                            "in_overlay": True,
                        })
                except Exception:
                    pass

            # Tabs inside overlay
            for tab in container_loc.locator("[role='tab']:visible").all():
                try:
                    label = _safe_label(tab, "")
                    key = f"tab::{label}"
                    if label and key not in seen:
                        seen.add(key)
                        overlay_elements.append({
                            "type": "tab",
                            "label": label,
                            "selector": _best_selector(tab),
                            "in_overlay": True,
                        })
                except Exception:
                    pass

            # Menu items inside overlay
            for mi in container_loc.locator(
                "[role='menuitem']:visible, [role='option']:visible"
            ).all():
                try:
                    label = _safe_label(mi, "")
                    key = f"menu_item::{label}"
                    if label and key not in seen:
                        seen.add(key)
                        overlay_elements.append({
                            "type": "menu_item",
                            "label": label,
                            "selector": _best_selector(mi),
                            "in_overlay": True,
                        })
                except Exception:
                    pass

            # Nav items inside overlay
            for ni in container_loc.locator(
                "nav button:visible, nav [role='button']:visible"
            ).all():
                try:
                    label = _safe_label(ni, "")
                    key = f"nav_item::{label}"
                    if label and key not in seen and len(label) < 30:
                        seen.add(key)
                        overlay_elements.append({
                            "type": "nav_item",
                            "label": label,
                            "selector": _best_selector(ni),
                            "in_overlay": True,
                        })
                except Exception:
                    pass

            # Accordions inside overlay
            for acc in container_loc.locator(
                "details > summary:visible, "
                ".accordion:visible, [data-accordion]:visible"
            ).all():
                try:
                    label = _safe_label(acc, "")
                    key = f"accordion::{label}"
                    if label and key not in seen:
                        seen.add(key)
                        overlay_elements.append({
                            "type": "accordion",
                            "label": label,
                            "selector": _best_selector(acc),
                            "in_overlay": True,
                        })
                except Exception:
                    pass
        finally:
            # Always clean up the marker attribute
            try:
                page.evaluate(_OVERLAY_CLEANUP_JS)
            except Exception:
                pass

        return overlay_elements

    except Exception:
        return []


# ---------------------------------------------------------------------------
# Element summary computation
# ---------------------------------------------------------------------------

def compute_element_summary(elements: list[dict]) -> dict:
    """Build a summary count of element types for a screen."""
    counts: Counter = Counter()
    for el in elements:
        counts[el["type"]] += 1
    summary: dict = {"total_interactive": len(elements)}
    for el_type in sorted(counts.keys()):
        summary[el_type] = counts[el_type]
    return summary


# ---------------------------------------------------------------------------
# State fingerprinting
# ---------------------------------------------------------------------------

def _build_overlay_fingerprint_js() -> str:
    """Build JS for the overlay signal in compute_fingerprint."""
    dialog_sel = DIALOG_SELECTORS_JS
    drawer_sel = ", ".join(
        f'"{s}"' for s in DRAWER_SELECTORS_JS[:4]  # open drawers/sidebars
    )
    return f"""() => {{
        const dialog = document.querySelector('{dialog_sel}');
        if (dialog) {{
            const style = getComputedStyle(dialog);
            if (style.display !== 'none' && style.visibility !== 'hidden') {{
                return 'dialog:' + (dialog.getAttribute('aria-label') || dialog.textContent?.trim().substring(0, 50) || 'open');
            }}
        }}
        const expanded = document.querySelectorAll('[aria-expanded="true"]');
        if (expanded.length > 0) {{
            const labels = [...expanded].map(e => e.textContent?.trim().substring(0, 30) || '').join(',');
            return 'expanded:' + labels;
        }}
        const drawerSels = [{drawer_sel}];
        for (const sel of drawerSels) {{
            const el = document.querySelector(sel);
            if (el) {{
                const style = getComputedStyle(el);
                if (style.display !== 'none' && style.visibility !== 'hidden') {{
                    return 'drawer:open';
                }}
            }}
        }}
        return '';
    }}"""


_OVERLAY_FP_JS = _build_overlay_fingerprint_js()


def compute_fingerprint(
    page: Page,
    elements: list[dict],
    base_origin: str,
    *,
    thorough: bool = True,
) -> str:
    """Unique identifier for a (url, DOM-state) pair.

    Uses multi-signal approach for SPA support:
    - Signal 1: interactive element labels
    - Signal 2: DOM structure (headings + active tab/selection)
    - Signal 3 (thorough): overlay/dialog state
    """
    url = normalize_url(page.url, base_origin)
    labels = sorted(e.get("label", "") for e in elements if e.get("label"))

    # Signal 1: interactive labels hash
    labels_hash = hashlib.md5("|".join(labels).encode()).hexdigest()[:8]

    # Signal 2: DOM structure (headings + active tab indicator)
    try:
        structure = page.evaluate("""() => {
            const headings = [...document.querySelectorAll('h1,h2,h3,[role=heading]')]
                .map(h => h.textContent?.trim()).filter(Boolean).join('|');
            const active = document.querySelector('[aria-selected=true],[data-state=active]');
            const activeLabel = active?.textContent?.trim() || '';
            return headings + '::' + activeLabel;
        }""")
    except Exception:
        structure = ""
    structure_hash = hashlib.md5(structure.encode()).hexdigest()[:6]

    # Signal 3: overlay state (thorough mode)
    overlay_hash = ""
    if thorough:
        try:
            overlay_state = page.evaluate(_OVERLAY_FP_JS)
            if overlay_state:
                overlay_hash = hashlib.md5(overlay_state.encode()).hexdigest()[:6]
        except Exception:
            pass

    if overlay_hash:
        return f"{url}::{labels_hash}::{structure_hash}::{overlay_hash}"
    return f"{url}::{labels_hash}::{structure_hash}"


# ---------------------------------------------------------------------------
# Non-href element exploration (modals, tabs, menu items, nav items, etc.)
# ---------------------------------------------------------------------------

# Element types that should be explored by clicking
CLICKABLE_TYPES = frozenset({
    "button", "tab", "menu_item", "nav_item",
    "icon_button", "accordion", "expandable", "drawer_trigger",
    "context_menu_trigger", "dialog_trigger",
    "toolbar_button", "tree_item", "fab",
    "card_action", "drawer_item", "generic_clickable",
    "role_button", "role_menuitem", "role_tab",
    "focusable_interactive", "snackbar_action",
})


def explore_clickable_element(
    page: Page,
    element: dict,
    current_screen_id: str,
    ctx: CrawlContext,
    depth: int,
    current_path: list,
    original_screen_fp: str,
    *,
    overlay_depth: int = 0,
) -> list[dict]:
    """
    Click a non-link element, check if it opened a new state, capture it.
    Returns a tuple of (new_screens, urls_to_enqueue) where new_screens is
    a list of screen dicts and urls_to_enqueue is a list of BFS queue entries
    for pages discovered via button clicks that change the URL.
    """
    selector = element.get("selector", "")
    if not selector:
        return [], []

    new_screens: list[dict] = []
    urls_to_enqueue: list[dict] = []

    try:
        page.locator(selector).first.click(timeout=3000)
        page.wait_for_timeout(500)

        try:
            page.wait_for_load_state("networkidle", timeout=2000)
        except Exception:
            pass

        scroll_to_bottom(page)
        new_elements = extract_interactive_elements(
            page, ctx.base_origin, page.url, thorough=ctx.thorough,
        )
        fp = compute_fingerprint(page, new_elements, ctx.base_origin, thorough=ctx.thorough)

        if fp in ctx.visited:
            _dismiss_overlay(page, original_screen_fp, ctx)
            return [], []

        ctx.visited.add(fp)
        screen_id = ctx.next_screen_id()
        screenshot_path = str(ctx.screenshots_dir / f"{screen_id}.png")

        # Use viewport-only screenshot when an overlay is visible to avoid
        # capturing the full page behind the dialog/drawer/modal.
        has_overlay = _is_overlay_visible(page)
        try:
            page.screenshot(
                path=screenshot_path,
                full_page=not has_overlay,
                timeout=5000,
            )
        except Exception:
            screenshot_path = ""

        new_path = current_path + [{
            "step": depth + 1,
            "from_screen": current_screen_id,
            "action": f"click:{element['type']}",
            "label": element.get("label", ""),
        }]

        screen: dict = {
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

        # --- Thorough: detect and explore overlays recursively ---
        if ctx.thorough:
            overlay_info = detect_overlay(page)
            if overlay_info:
                screen["overlay"] = overlay_info
                overlay_els = extract_overlay_elements(
                    page, ctx.base_origin, page.url, ctx.thorough,
                )
                if overlay_els:
                    screen["overlay_elements"] = overlay_els

                    if overlay_depth < ctx.max_overlay_depth:
                        for oel in overlay_els:
                            if oel["type"] not in CLICKABLE_TYPES and oel["type"] != "link":
                                continue
                            if not oel.get("selector"):
                                continue
                            sub_screens, sub_urls = explore_clickable_element(
                                page, oel, screen_id,
                                ctx,
                                depth + 1, new_path,
                                original_screen_fp=fp,
                                overlay_depth=overlay_depth + 1,
                            )
                            new_screens.extend(sub_screens)
                            urls_to_enqueue.extend(sub_urls)
            else:
                # No overlay - the click opened a new page (URL changed).
                # Enqueue it for BFS so its own links/buttons get explored.
                clicked_url = page.url
                norm_clicked = normalize_url(clicked_url, ctx.base_origin)
                if (
                    is_internal_url(clicked_url, ctx.base_origin)
                    and norm_clicked not in ctx.visited
                ):
                    urls_to_enqueue.append({
                        "url": clicked_url,
                        "depth": depth + 1,
                        "path": new_path,
                        "reached_via": {
                            "from_screen": current_screen_id,
                            "action": f"click:{element['type']}",
                            "label": element.get("label", ""),
                        },
                    })

            screen["element_summary"] = compute_element_summary(new_elements)

        new_screens.insert(0, screen)

        # Dismiss modal / restore original state
        _dismiss_overlay(page, original_screen_fp, ctx)

        return new_screens, urls_to_enqueue

    except Exception:
        return [], []


def _dismiss_overlay(
    page: Page,
    original_fp: str,
    ctx: CrawlContext,
) -> None:
    """Try to dismiss an overlay/modal/sheet and restore the original screen state."""
    # Step 1: try Escape
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
    except Exception:
        pass

    # Lightweight check: is the overlay gone?
    if not _is_overlay_visible(page):
        return

    # Step 2: try clicking close button inside overlay
    if ctx.thorough:
        close_selectors = [
            "[aria-label*='close' i]:visible",
            "[aria-label*='chiudi' i]:visible",
            "[class*='close']:visible",
            "[class*='Close']:visible",
            "dialog button:first-of-type:visible",
        ]
        for cs in close_selectors:
            try:
                close_btn = page.locator(cs).first
                if close_btn.is_visible(timeout=300):
                    close_btn.click(timeout=1000)
                    page.wait_for_timeout(400)
                    if not _is_overlay_visible(page):
                        return
            except Exception:
                pass

    # Step 3: try clicking the backdrop (top-left corner)
    try:
        page.mouse.click(10, 10)
        page.wait_for_timeout(400)
    except Exception:
        pass


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

    # Aggregate element type counts
    type_totals: Counter = Counter()
    for s in screens.values():
        for el in s.get("elements", []):
            type_totals[el["type"]] += 1

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
        "element_type_totals": dict(type_totals.most_common()),
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
# Browser context setup
# ---------------------------------------------------------------------------

def create_context(
    browser: Browser,
    *,
    mobile: bool,
    width: int,
    height: int,
    auth_path: str | None = None,
) -> BrowserContext:
    """Create a browser context with optional mobile viewport and auth state."""
    kwargs: dict = {}

    if mobile:
        kwargs.update({
            "viewport": {"width": width, "height": height},
            "device_scale_factor": 3,
            "is_mobile": True,
            "has_touch": True,
        })

    if auth_path and Path(auth_path).exists():
        kwargs["storage_state"] = auth_path

    context = browser.new_context(**kwargs)
    context.on("page", lambda p: p.on("dialog", lambda d: d.dismiss()))
    return context


# ---------------------------------------------------------------------------
# Main BFS loop
# ---------------------------------------------------------------------------

def crawl(
    start_url: str,
    output_dir: str,
    max_depth: int,
    max_screens: int,
    *,
    mobile: bool = True,
    width: int = 390,
    height: int = 844,
    auth: str | None = None,
    thorough: bool = True,
) -> None:
    # Validate start URL scheme
    parsed_start = urlparse(start_url)
    if parsed_start.scheme not in ("http", "https"):
        raise SystemExit(f"Error: only http/https URLs are supported, got: {parsed_start.scheme}")

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

    base_origin = f"{parsed_start.scheme}://{parsed_start.netloc}"

    ctx = CrawlContext(
        base_origin=base_origin,
        output_dir=output_dir,
        screenshots_dir=screenshots_dir,
        thorough=thorough,
        log=log,
    )

    screens: dict[str, dict] = {}

    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(headless=False)
        context = create_context(
            browser, mobile=mobile, width=width, height=height, auth_path=auth,
        )
        page: Page = context.new_page()

        # --- Login phase ---
        auth_loaded = bool(auth and Path(auth).exists())
        log.info("Navigating to %s", start_url)
        page.goto(start_url)
        page.wait_for_load_state("networkidle", timeout=15000)

        if auth_loaded:
            log.info("Auth state loaded from %s", auth)
            elements_check = extract_interactive_elements(
                page, base_origin, page.url, thorough=thorough,
            )
            labels_check = [e.get("label", "").lower() for e in elements_check]
            login_indicators = ["accedi", "login", "sign in", "registrati", "sign up"]
            still_on_login = any(
                ind in label for ind in login_indicators for label in labels_check
            )
            if still_on_login:
                log.warning("Auth state expired - manual login required")
                auth_loaded = False

        if not auth_loaded:
            print("\n" + "=" * 60)
            print("Browser aperto. Effettua il login se necessario,")
            print("poi premi Invio per avviare il crawl...")
            print("=" * 60 + "\n")
            input()
            page.wait_for_timeout(1000)

            post_login_elements = extract_interactive_elements(
                page, base_origin, page.url, thorough=thorough,
            )
            labels_post = [e.get("label", "").lower() for e in post_login_elements]
            login_indicators = ["accedi", "login", "sign in", "registrati", "sign up"]
            still_on_login = any(
                ind in label for ind in login_indicators for label in labels_post
            )
            if still_on_login:
                log.warning("Still on login page. Press Enter again after logging in...")
                input()
                page.wait_for_timeout(1000)

        # Save auth state for future crawls (owner-only permissions)
        auth_save_path = output_path / "auth.json"
        try:
            context.storage_state(path=str(auth_save_path))
            try:
                os.chmod(str(auth_save_path), 0o600)
            except OSError:
                pass  # Windows may not support chmod
            log.info("Auth state saved to %s", auth_save_path)
        except Exception as exc:
            log.warning("Could not save auth state: %s", exc)

        # Capture current page as root (don't re-navigate - preserves auth)
        root_url = page.url
        mode_label = "THOROUGH" if thorough else "BASIC"
        log.info(
            "BFS crawl started [%s] from %s. max_depth=%d max_screens=%d",
            mode_label, root_url, max_depth, max_screens,
        )
        start_time = time.time()

        queue: deque[dict] = deque([{
            "url": root_url,
            "depth": 0,
            "path": [],
            "reached_via": None,
            "skip_navigation": True,
        }])

        # --- BFS ---
        while queue:
            if ctx.screen_counter >= max_screens:
                log.info("max_screens limit reached (%d)", max_screens)
                break

            state = queue.popleft()
            url = state["url"]
            depth = state["depth"]
            path = state["path"]

            if depth > max_depth:
                continue

            # Navigate only if not using the current page
            if not state.get("skip_navigation"):
                try:
                    page.goto(url, wait_until="networkidle", timeout=15000)
                except Exception as exc:
                    log.warning("Navigation failed for %s: %s", url, exc)
                    continue

            scroll_to_bottom(page)
            elements = extract_interactive_elements(
                page, base_origin, page.url, thorough=thorough,
            )

            # Thorough: detect additional clickables via JS
            if thorough:
                js_clickables = detect_all_clickables(page)
                existing_labels = {
                    f"{e['type']}::{e.get('label', '')}" for e in elements
                }
                for jc in js_clickables:
                    key = f"{jc['type']}::{jc.get('label', '')}"
                    if key not in existing_labels and jc.get("label"):
                        existing_labels.add(key)
                        elements.append(jc)

            # Thorough: explore hamburger/drawer menus
            # (re-navigate after to restore page state for fingerprinting)
            if thorough:
                drawer_items, drawer_screen = explore_hamburger_menu(
                    page, base_origin, page.url, thorough, log, ctx=ctx,
                )
                if drawer_screen is not None:
                    drawer_screen["depth"] = depth
                    drawer_screen["min_clicks_from_root"] = depth + 1
                    drawer_screen["path_from_root"] = path + [{
                        "step": depth + 1,
                        "from_screen": "pending",
                        "action": "open_drawer",
                        "label": "hamburger_menu",
                    }]
                    screens[drawer_screen["id"]] = drawer_screen
                    log.info("[%d] %s  (drawer menu)", ctx.screen_counter - 1, drawer_screen["id"])
                if drawer_items:
                    existing_labels_set = {
                        f"{e['type']}::{e.get('label', '')}" for e in elements
                    }
                    for di in drawer_items:
                        key = f"{di['type']}::{di.get('label', '')}"
                        if key not in existing_labels_set:
                            existing_labels_set.add(key)
                            elements.append(di)
                    # Re-navigate to restore clean page state after drawer interaction
                    try:
                        page.goto(url, wait_until="networkidle", timeout=10000)
                        scroll_to_bottom(page)
                    except Exception:
                        pass

            fp = compute_fingerprint(page, elements, base_origin, thorough=thorough)

            if fp in ctx.visited:
                log.debug("Skip visited state: %s", fp[:60])
                continue
            ctx.visited.add(fp)

            screen_id = ctx.next_screen_id()
            screenshot_path = str(screenshots_dir / f"{screen_id}.png")

            try:
                page.screenshot(path=screenshot_path, full_page=True, timeout=8000)
            except Exception as exc:
                log.warning("Screenshot failed for %s: %s", url, exc)
                screenshot_path = ""

            log.info("[%d] %s  %s  (%d elements)", ctx.screen_counter - 1, screen_id, page.url, len(elements))

            # Patch drawer_screen's from_screen now that we have screen_id
            if thorough and drawer_screen is not None and drawer_screen["id"] in screens:
                for step in drawer_screen.get("path_from_root", []):
                    if step.get("from_screen") == "pending":
                        step["from_screen"] = screen_id
                if drawer_screen.get("reached_via", {}).get("from_screen") is None:
                    drawer_screen["reached_via"]["from_screen"] = screen_id

            # Enqueue link children + mark leads_to as None (resolved post-crawl)
            enriched_elements = []
            for el in elements:
                enriched = dict(el)
                if el["type"] in ("link", "drawer_item") and el.get("href"):
                    enriched["leads_to"] = None
                    if depth < max_depth and ctx.screen_counter < max_screens:
                        queue.append({
                            "url": el.get("href", ""),
                            "depth": depth + 1,
                            "path": path + [{
                                "step": depth + 1,
                                "from_screen": screen_id,
                                "action": f"click:{el['type']}",
                                "label": el.get("label", ""),
                            }],
                            "reached_via": {
                                "from_screen": screen_id,
                                "action": f"click:{el['type']}",
                                "label": el.get("label", ""),
                            },
                        })
                enriched_elements.append(enriched)

            # Explore clickable non-link elements
            if depth < max_depth:
                for el in elements:
                    if el["type"] not in CLICKABLE_TYPES:
                        continue
                    if ctx.screen_counter >= max_screens:
                        break
                    click_screens, click_urls = explore_clickable_element(
                        page, el, screen_id,
                        ctx,
                        depth, path,
                        original_screen_fp=fp,
                    )
                    for ns in click_screens:
                        screens[ns["id"]] = ns
                        log.info(
                            "[%d] %s  (via click:%s '%s')",
                            ctx.screen_counter - 1, ns["id"],
                            el.get("type", ""), el.get("label", ""),
                        )
                    # Enqueue pages discovered via button clicks for BFS
                    for cu in click_urls:
                        if cu["depth"] <= max_depth:
                            queue.append(cu)

                    # Re-navigate back to current URL after each click
                    try:
                        page.goto(url, wait_until="networkidle", timeout=10000)
                        scroll_to_bottom(page)
                    except Exception:
                        break

            screen_data: dict = {
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

            if thorough:
                screen_data["element_summary"] = compute_element_summary(enriched_elements)

            screens[screen_id] = screen_data

        browser.close()

    # --- Post-crawl: resolve leads_to for link elements ---
    url_to_screen: dict[str, str] = {
        normalize_url(s["url"], base_origin): sid
        for sid, s in screens.items()
    }
    for screen in screens.values():
        for el in screen.get("elements", []):
            if el["type"] in ("link", "drawer_item") and el.get("href"):
                el["leads_to"] = url_to_screen.get(normalize_url(el["href"], base_origin))

    # --- Build sitemap ---
    metrics = compute_meta_metrics(screens)
    elapsed = round(time.time() - start_time, 1)

    sitemap = {
        "meta": {
            "app_url": start_url,
            "explored_at": datetime.now(timezone.utc).isoformat(),
            "crawl_duration_seconds": elapsed,
            "thorough_mode": thorough,
            **metrics,
        },
        "screens": screens,
        "navigation_graph": build_navigation_graph(screens),
        "workflows": build_workflows(screens),
    }

    sitemap_path = output_path / "sitemap.json"
    with sitemap_path.open("w", encoding="utf-8") as f:
        json.dump(sitemap, f, indent=2, ensure_ascii=False)

    type_totals = metrics.get("element_type_totals", {})

    print("\n" + "=" * 60)
    print(f"Crawl completed in {elapsed}s")
    print(f"  Mode:                {'THOROUGH' if thorough else 'BASIC'}")
    print(f"  Screens found:       {metrics.get('total_screens', 0)}")
    print(f"  Total actions:       {metrics.get('total_actions', 0)}")
    print(f"  Max clicks (worst):  {metrics.get('max_clicks_to_reach_any_screen', 0)}")
    print(f"  Avg clicks:          {metrics.get('avg_clicks_to_reach_any_screen', 0)}")
    print(f"  Deepest screen:      {metrics.get('deepest_screen', {}).get('title', '')} "
          f"({metrics.get('deepest_screen', {}).get('min_clicks', 0)} clicks)")
    if type_totals:
        print("  Element types found:")
        for etype, count in sorted(type_totals.items(), key=lambda x: -x[1]):
            print(f"    {etype:.<30} {count}")
    print(f"\nOutput: {sitemap_path}")
    if auth_save_path.exists():
        print(f"Auth state: {auth_save_path} (use --auth to skip login next time)")
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
        mobile=args.mobile,
        width=args.width,
        height=args.height,
        auth=args.auth,
        thorough=args.thorough,
    )
