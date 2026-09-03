"""Snapshot, diff, carry and check for incremental X-ray runs.

An incremental run is only as trustworthy as the mechanical layer under it:
if the diff misses a changed symbol, a stale claim ships. Every case here
pins one property that mechanical layer must have.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/codebase-xray/skills/xray-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ast_parser import parse_file  # noqa: E402

PY_SOURCE = textwrap.dedent(
    '''
    """Module docstring."""
    import os
    from orders.models import Order


    CONSTANT = 3


    class OrderService:
        """Places orders."""

        def __init__(self, repo):
            self.repo = repo

        def place(self, order):
            """Place one order."""
            self.repo.save(order)
            return order.id

        def cancel(self, order_id):
            self.repo.delete(order_id)


    def retry_policy(attempts=3):
        return attempts * 2
    '''
).lstrip()


def write(tmp: Path, rel: str, content: str) -> Path:
    path = tmp / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class EndLineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="xray-endline-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_python_class_and_method_carry_an_end_line(self):
        path = write(self.tmp, "service.py", PY_SOURCE)
        result = parse_file(path)
        klass = next(c for c in result.classes if c.name == "OrderService")
        place = next(m for m in klass.methods if m.name == "place")
        func = next(f for f in result.functions if f.name == "retry_policy")

        self.assertIsNotNone(klass.end_line)
        self.assertIsNotNone(place.end_line)
        self.assertIsNotNone(func.end_line)
        # The class span encloses every one of its methods.
        self.assertGreaterEqual(klass.end_line, max(m.end_line for m in klass.methods))
        # place() ends before cancel() begins.
        cancel = next(m for m in klass.methods if m.name == "cancel")
        self.assertLess(place.end_line, cancel.line_number)


JS_SOURCE = textwrap.dedent(
    """
    import { Order } from './models';

    export class Cart {
      add(item) { return item; }
      total() { return 0; }
    }

    export function checkout(cart) {
      return cart.total();
    }
    """
).lstrip()


def run_script(*args, cwd=None):
    """Invoke snapshot.py as the workflows do, and return (code, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "snapshot.py"), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )
    return proc.returncode, proc.stdout, proc.stderr


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="xray-manifest-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / "src"
        write(self.src, "orders/service.py", PY_SOURCE)
        write(self.src, "web/cart.js", JS_SOURCE)
        write(self.src, "README.md", "# Orders\n\nSee `orders/service.py`.\n")
        write(self.src, ".env", "SECRET_TOKEN=abc123\n")
        write(self.src, "node_modules/pkg/index.js", "module.exports = 1;\n")

    def manifest(self):
        out = self.tmp / "manifest.json"
        code, _, err = run_script("write", self.src, "--out", out)
        self.assertEqual(code, 0, err)
        return json.loads(out.read_text(encoding="utf-8"))

    def test_source_doc_and_symbols_are_recorded(self):
        files = self.manifest()["files"]
        service = next(v for k, v in files.items() if k.endswith("orders/service.py"))
        self.assertEqual(service["language"], "python")
        self.assertIn("OrderService", service["symbols"])
        self.assertIn("OrderService.place", service["symbols"])
        self.assertIn("retry_policy", service["symbols"])
        self.assertEqual(service["symbols"]["OrderService.place"]["kind"], "method")

        readme = next(v for k, v in files.items() if k.endswith("README.md"))
        self.assertIsNone(readme["language"])
        self.assertEqual(readme["symbols"], {})
        for entry in files.values():
            for field in ("size", "mtime", "hash", "lines"):
                self.assertIn(field, entry)

    def test_a_class_span_encloses_its_methods(self):
        files = self.manifest()["files"]
        service = next(v for k, v in files.items() if k.endswith("orders/service.py"))
        klass = service["symbols"]["OrderService"]
        place = service["symbols"]["OrderService.place"]
        self.assertLessEqual(klass["start"], place["start"])
        self.assertGreaterEqual(klass["end"], place["end"])

    def test_a_span_is_inferred_when_the_parser_gives_no_end(self):
        files = self.manifest()["files"]
        cart = next(v for k, v in files.items() if k.endswith("web/cart.js"))
        self.assertIn("Cart", cart["symbols"])
        for symbol in cart["symbols"].values():
            self.assertGreaterEqual(symbol["end"], symbol["start"])

    def test_forbidden_and_excluded_paths_never_enter_the_manifest(self):
        paths = list(self.manifest()["files"])
        self.assertFalse([p for p in paths if p.endswith(".env")])
        self.assertFalse([p for p in paths if "node_modules" in p])

    def test_the_manifest_is_deterministic(self):
        first = self.tmp / "a.json"
        second = self.tmp / "b.json"
        run_script("write", self.src, "--out", first)
        run_script("write", self.src, "--out", second)
        a = json.loads(first.read_text(encoding="utf-8"))
        b = json.loads(second.read_text(encoding="utf-8"))
        a.pop("created_at")
        b.pop("created_at")
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_editing_one_method_leaves_the_others_alone(self):
        before = self.manifest()["files"]
        path = self.src / "orders/service.py"
        path.write_text(
            PY_SOURCE.replace("self.repo.delete(order_id)", "self.repo.delete(order_id)\n        return True"),
            encoding="utf-8",
        )
        after = self.manifest()["files"]
        key = next(k for k in before if k.endswith("orders/service.py"))
        old, new = before[key]["symbols"], after[key]["symbols"]
        self.assertEqual(old["OrderService.place"]["hash"], new["OrderService.place"]["hash"])
        self.assertNotEqual(old["OrderService.cancel"]["hash"], new["OrderService.cancel"]["hash"])
        # A method is part of its class, so the class hash moves with it.
        self.assertNotEqual(old["OrderService"]["hash"], new["OrderService"]["hash"])

    def test_internal_imports_are_recorded(self):
        files = self.manifest()["files"]
        service = next(v for k, v in files.items() if k.endswith("orders/service.py"))
        self.assertIn("orders.models", service["imports"])


if __name__ == "__main__":
    unittest.main()
