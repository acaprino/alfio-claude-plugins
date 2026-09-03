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


if __name__ == "__main__":
    unittest.main()
