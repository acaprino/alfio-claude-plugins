"""The codebase-xray script suite, exercised on small sources.

These scripts are what the X-ray method tells every phase to run instead of
reading files by hand, and until this file they had no test at all. Each case
here pins a behaviour the first review found wrong or unverified: the
classifier calling every file with an author line security-critical, the
TypeScript parser missing arrow-function methods, the Java parser missing
nested types, duplicate import modules in the CLI output, and a documentation
scan that shouted "ALL DOCUMENTATION SHOULD BE CONSIDERED UNVERIFIED" at any
project not born with this toolkit's marker convention.

Tree-sitter is optional for the scripts and absent on CI, so the cases that
need it are skipped there and the regex fallback is what CI exercises.
"""

import json
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

import classifier  # noqa: E402
from ast_parser import parse_file  # noqa: E402
from languages._treesitter import get_parser  # noqa: E402
from usage_finder import find_all_usages  # noqa: E402

HAVE_TREE_SITTER = get_parser("typescript") is not None

TYPESCRIPT = textwrap.dedent(
    """
    import { Router } from "express";
    import type { User } from "./types";
    const DEFAULT_TTL = 300;
    export interface Repo<T> { get(id: string): Promise<T | null>; }
    export enum Status { Active = "active", Archived = "archived" }
    export type Handler = (u: User) => void;
    export class UserService implements Repo<User> {
      private cache = new Map<string, User>();
      constructor(private readonly router: Router) {}
      async get(id: string): Promise<User | null> { return this.cache.get(id) ?? null; }
      onUser = (u: User): void => { this.cache.set(u.id, u); };
    }
    export const makeService = (r: Router) => new UserService(r);
    """
)

JAVA = textwrap.dedent(
    """
    package com.example;
    import java.util.Map;
    import java.util.HashMap;
    public class Svc<T extends Comparable<T>> {
        private static final int MAX = 10;
        private final Map<String, T> store = new HashMap<>();
        @Override
        public String toString() { return "Svc"; }
        public synchronized void put(String k,
                                     T v) { store.put(k, v); }
        public static class Inner { public int x; }
        interface Listener { void on(String s); }
    }
    """
)

RUST = textwrap.dedent(
    """
    use std::collections::HashMap;
    pub const MAX: usize = 10;
    pub struct Store<'a, T: Clone> { items: HashMap<&'a str, T> }
    pub trait Repo { fn get(&self, k: &str) -> Option<String>; }
    impl<'a, T: Clone> Repo for Store<'a, T> { fn get(&self, k: &str) -> Option<String> { None } }
    """
)

PYTHON = textwrap.dedent(
    """
    import os
    from pathlib import Path

    class Loader:
        def read(self, path: Path) -> str:
            return path.read_text()

    def helper(x: int) -> int:
        return x + 1
    """
)


def _write(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


class ClassifierTests(unittest.TestCase):
    def test_an_author_line_is_not_a_security_signal(self):
        result = classifier.classify_from_content(
            "author = 'someone'\nauthored_by = 'x'\nimport os\n", "meta.py"
        )
        self.assertNotEqual(result.classification, classifier.Classification.CRITICAL)
        self.assertEqual(result.critical_patterns_found, [])

    def test_authentication_still_is(self):
        result = classifier.classify_from_content(
            "def authenticate(user, token):\n    return True\n", "login.py"
        )
        self.assertEqual(result.classification, classifier.Classification.CRITICAL)

    def test_an_ordinary_import_count_is_not_high_complexity(self):
        imports = "\n".join(f"import mod{i}" for i in range(6))
        body = "\n".join(f"value_{i} = {i}" for i in range(150))
        result = classifier.classify_from_content(f"{imports}\n{body}\n", "plain.py")
        self.assertEqual(result.classification, classifier.Classification.STANDARD)
        self.assertFalse(result.verification_required)


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.temp, ignore_errors=True))

    def test_python_uses_the_stdlib_parser(self):
        result = parse_file(_write(self.temp, "mod.py", PYTHON))
        self.assertIn("parser=stdlib-ast", result.notes)
        self.assertEqual([c.name for c in result.classes], ["Loader"])
        self.assertEqual([m.name for m in result.classes[0].methods], ["read"])
        self.assertIn("helper", [f.name for f in result.functions])

    def test_typescript_finds_the_class_on_either_parser(self):
        result = parse_file(_write(self.temp, "svc.ts", TYPESCRIPT))
        self.assertIn("UserService", [c.name for c in result.classes])
        self.assertIn("UserService", result.exported_symbols)

    @unittest.skipUnless(HAVE_TREE_SITTER, "tree-sitter not installed")
    def test_typescript_tree_sitter_sees_arrow_methods_and_const_functions(self):
        result = parse_file(_write(self.temp, "svc.ts", TYPESCRIPT))
        self.assertIn("parser=tree-sitter (ts)", result.notes)
        service = next(c for c in result.classes if c.name == "UserService")
        self.assertIn("get", [m.name for m in service.methods])
        self.assertIn("onUser", [m.name for m in service.methods])
        self.assertIn("makeService", [f.name for f in result.functions])
        self.assertEqual(
            {c.kind for c in result.classes}, {"class", "interface", "enum", "type-alias"}
        )

    def test_java_finds_the_class_on_either_parser(self):
        result = parse_file(_write(self.temp, "Svc.java", JAVA))
        self.assertIn("Svc", [c.name for c in result.classes])

    @unittest.skipUnless(HAVE_TREE_SITTER, "tree-sitter not installed")
    def test_java_tree_sitter_sees_nested_types_and_multiline_methods(self):
        result = parse_file(_write(self.temp, "Svc.java", JAVA))
        names = [c.name for c in result.classes]
        self.assertIn("Svc.Inner", names)
        self.assertIn("Svc.Listener", names)
        outer = next(c for c in result.classes if c.name == "Svc")
        self.assertEqual({m.name for m in outer.methods}, {"toString", "put"})
        listener = next(c for c in result.classes if c.name == "Svc.Listener")
        self.assertEqual(listener.kind, "interface")

    def test_rust_finds_struct_and_trait(self):
        result = parse_file(_write(self.temp, "lib.rs", RUST))
        names = [c.name for c in result.classes]
        self.assertIn("Store", names)
        self.assertIn("Repo", names)
        self.assertIn("MAX", result.constants)

    def test_cli_output_lists_each_import_module_once(self):
        source = _write(self.temp, "Svc.java", JAVA)
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "ast_parser.py"), str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        external = payload["imports"]["external"]
        self.assertEqual(len(external), len(set(external)), external)


class UsageFinderTests(unittest.TestCase):
    def test_finds_import_and_reference(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        _write(temp, "core.py", "class Engine:\n    pass\n")
        _write(temp, "app.py", "from core import Engine\n\nengine = Engine()\n")
        result = find_all_usages("Engine", temp / "core.py", temp)
        self.assertGreaterEqual(len(result.usages), 2)
        self.assertTrue(any("app.py" in str(u) for u in result.usages), result.usages)


class DocReviewTests(unittest.TestCase):
    def test_a_project_without_markers_is_not_shouted_at(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        docs = temp / "docs"
        docs.mkdir()
        _write(docs, "guide.md", "# Guide\n\nPlain documentation with no markers.\n")
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "doc_review.py"), "scan", "--path", "docs"],
            cwd=temp,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertNotIn("ALL DOCUMENTATION SHOULD BE CONSIDERED UNVERIFIED", completed.stdout)
        self.assertIn("does not use the", completed.stdout)
        self.assertIn("not used by this project", completed.stdout)
        self.assertNotIn("Phase 8", completed.stdout + completed.stderr)


class CommentAnalysisTests(unittest.TestCase):
    def test_analyze_runs_on_a_python_file(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        source = _write(temp, "mod.py", '"""Module docstring."""\n\n# increment x\nx = 1\n')
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "rewrite_comments.py"), "analyze", str(source), "--report"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Comment Analysis", completed.stdout)


if __name__ == "__main__":
    unittest.main()
