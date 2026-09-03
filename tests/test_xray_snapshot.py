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

    def test_overloaded_methods_share_a_widened_span(self):
        source = textwrap.dedent(
            """
            export class Cart {
              place(item) { return item; }
              place(item, qty) { return item * qty; }
            }
            """
        ).lstrip()
        files = self.manifest_of("cart.ts", source)
        span = files["symbols"]["Cart.place"]
        # A single recorded span covers both overloads, from the first
        # method's start to the second method's end.
        self.assertLessEqual(span["start"], 2)
        self.assertGreaterEqual(span["end"], 3)

        edited = source.replace(
            "place(item, qty) { return item * qty; }",
            "place(item, qty) { return item * qty * 2; }",
        )
        edited_files = self.manifest_of("cart.ts", edited)
        self.assertNotEqual(span["hash"], edited_files["symbols"]["Cart.place"]["hash"])

        # Editing the FIRST overload must also move the widened span's hash.
        # Before the widening fix, a second `record()` call overwrote the
        # first overload's span entirely, so an edit confined to it changed
        # no hash and the loss went unnoticed.
        edited_first = source.replace(
            "place(item) { return item; }",
            "place(item) { return item * 1; }",
        )
        edited_first_files = self.manifest_of("cart.ts", edited_first)
        self.assertNotEqual(span["hash"], edited_first_files["symbols"]["Cart.place"]["hash"])

    def manifest_of(self, rel: str, content: str) -> dict:
        write(self.src, rel, content)
        files = self.manifest()["files"]
        return next(v for k, v in files.items() if k.endswith(rel))


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="xray-compare-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / "src"
        write(self.src, "orders/service.py", PY_SOURCE)
        write(self.src, "web/cart.js", JS_SOURCE)
        import snapshot
        self.snapshot = snapshot
        self.manifest = snapshot.build_manifest(self.src)

    def key(self, suffix):
        return next(k for k in self.manifest["files"] if k.endswith(suffix))

    def test_an_untouched_tree_has_nothing_modified(self):
        result = self.snapshot.compare_files(self.manifest, self.src)
        self.assertEqual(result["modified"], [])
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])

    def test_added_and_removed_files_are_seen(self):
        write(self.src, "orders/repo.py", "class Repo:\n    pass\n")
        (self.src / "web/cart.js").unlink()
        result = self.snapshot.compare_files(self.manifest, self.src)
        self.assertTrue(any(p.endswith("orders/repo.py") for p in result["added"]))
        self.assertTrue(any(p.endswith("web/cart.js") for p in result["removed"]))

    def test_a_touched_but_identical_file_is_unchanged(self):
        path = self.src / "orders/service.py"
        os.utime(path, (path.stat().st_atime + 120, path.stat().st_mtime + 120))
        result = self.snapshot.compare_files(self.manifest, self.src)
        self.assertEqual(result["modified"], [])
        self.assertIn(self.key("orders/service.py"), result["unchanged"])

    def test_verify_hashes_everything_and_still_finds_no_change(self):
        result = self.snapshot.compare_files(self.manifest, self.src, verify=True)
        self.assertEqual(result["modified"], [])

    def test_a_real_edit_is_modified(self):
        path = self.src / "orders/service.py"
        path.write_text(PY_SOURCE.replace("return attempts * 2", "return attempts * 3"), encoding="utf-8")
        result = self.snapshot.compare_files(self.manifest, self.src)
        self.assertEqual(result["modified"], [self.key("orders/service.py")])

    def test_symbol_level_classification(self):
        path = self.src / "orders/service.py"
        edited = PY_SOURCE.replace(
            "    def cancel(self, order_id):\n        self.repo.delete(order_id)\n",
            "    def refund(self, order_id):\n        self.repo.refund(order_id)\n",
        ).replace("return attempts * 2", "return attempts * 3")
        path.write_text(edited, encoding="utf-8")
        files = self.snapshot.compare_files(self.manifest, self.src)
        symbols = self.snapshot.compare_symbols(self.manifest, files)
        added = {s["symbol"] for s in symbols["added"]}
        removed = {s["symbol"] for s in symbols["removed"]}
        changed = {s["symbol"] for s in symbols["changed"]}
        self.assertIn("OrderService.refund", added)
        self.assertIn("OrderService.cancel", removed)
        self.assertIn("retry_policy", changed)
        self.assertIn("OrderService", changed)
        self.assertNotIn("OrderService.place", changed)

    def test_renumber_records_the_old_span_and_the_new_start(self):
        path = self.src / "orders/service.py"
        # Two extra lines above the class push everything below it down.
        path.write_text(PY_SOURCE.replace("CONSTANT = 3", "CONSTANT = 3\nEXTRA = 1\nMORE = 2"), encoding="utf-8")
        files = self.snapshot.compare_files(self.manifest, self.src)
        symbols = self.snapshot.compare_symbols(self.manifest, files)
        entries = symbols["renumber"][self.key("orders/service.py")]
        place = next(e for e in entries if e["symbol"] == "OrderService.place")
        self.assertEqual(place["start_new"], place["start_old"] + 2)
        self.assertGreaterEqual(place["end_old"], place["start_old"])


class BlastRadiusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="xray-radius-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / "src"
        write(self.src, "orders/service.py", PY_SOURCE)
        write(self.src, "orders/models.py", "class Order:\n    pass\n")
        write(
            self.src,
            "api/routes.py",
            "from orders.service import OrderService\n\n\ndef handler():\n    return OrderService(None)\n",
        )
        write(self.src, "reports/monthly.py", "import csv\n\n\ndef build():\n    return csv\n")
        import snapshot
        self.snapshot = snapshot
        self.manifest = snapshot.build_manifest(self.src)

    def radius(self):
        files = self.snapshot.compare_files(self.manifest, self.src)
        symbols = self.snapshot.compare_symbols(self.manifest, files)
        index = self.snapshot.build_import_index(self.manifest, files, symbols)
        return files, self.snapshot.blast_radius(index, files, symbols)

    def test_a_pure_line_shift_puts_nobody_in_the_radius(self):
        path = self.src / "orders/service.py"
        path.write_text(PY_SOURCE.replace("CONSTANT = 3", "CONSTANT = 3\nEXTRA = 1"), encoding="utf-8")
        files, importers = self.radius()
        self.assertTrue(any(p.endswith("orders/service.py") for p in files["modified"]))
        self.assertEqual(importers, [])

    def test_a_direct_importer_is_in_the_radius(self):
        path = self.src / "orders/service.py"
        path.write_text(PY_SOURCE.replace("return attempts * 2", "return attempts * 4"), encoding="utf-8")
        _, importers = self.radius()
        self.assertTrue(any(entry["file"].endswith("api/routes.py") for entry in importers))

    def test_an_unrelated_file_is_not(self):
        path = self.src / "orders/service.py"
        path.write_text(PY_SOURCE.replace("return attempts * 2", "return attempts * 4"), encoding="utf-8")
        _, importers = self.radius()
        self.assertFalse(any(entry["file"].endswith("reports/monthly.py") for entry in importers))

    def test_the_radius_is_one_hop_only(self):
        # models.py changes. service.py imports it, routes.py imports service.py.
        # Only service.py is in the radius: routes.py is two hops away.
        (self.src / "orders/models.py").write_text("class Order:\n    id = 0\n", encoding="utf-8")
        _, importers = self.radius()
        names = {entry["file"] for entry in importers}
        self.assertTrue(any(n.endswith("orders/service.py") for n in names))
        self.assertFalse(any(n.endswith("api/routes.py") for n in names))

    def test_a_relative_javascript_import_resolves(self):
        write(self.src, "web/models.js", "export class Order {}\n")
        write(self.src, "web/cart.js", JS_SOURCE)
        self.manifest = self.snapshot.build_manifest(self.src)
        (self.src / "web/models.js").write_text("export class Order { id = 0; }\n", encoding="utf-8")
        _, importers = self.radius()
        self.assertTrue(any(entry["file"].endswith("web/cart.js") for entry in importers))


if __name__ == "__main__":
    unittest.main()
