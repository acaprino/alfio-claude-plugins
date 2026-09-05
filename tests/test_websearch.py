"""Tests for the research plugin's optional serper.dev backend script.

Stdlib only. The network is never touched: `main()` takes an injectable
fetcher, and the payload/render functions are pure.
"""
import importlib.util
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins" / "research" / "skills" / "web-search-techniques" / "scripts" / "websearch.py"


def load_module():
    spec = importlib.util.spec_from_file_location("websearch", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ws = load_module()

SAMPLE_SEARCH = {
    "searchParameters": {"q": "apple inc", "type": "search"},
    "answerBox": {"answer": "Cupertino", "title": "Apple HQ", "link": "https://example.com/hq"},
    "knowledgeGraph": {"title": "Apple", "type": "Company", "description": "Tech company"},
    "organic": [
        {"title": "Apple", "link": "https://www.apple.com/", "snippet": "Official site", "position": 1},
        {"title": "Apple Inc. news", "link": "https://news.example.com/a", "snippet": "Latest",
         "position": 2, "date": "Aug 20, 2026"},
    ],
    "peopleAlsoAsk": [{"question": "Who founded Apple?", "snippet": "Jobs, Wozniak, Wayne",
                       "link": "https://example.com/founders"}],
    "relatedSearches": [{"query": "apple stock"}],
}

SAMPLE_NEWS = {
    "news": [
        {"title": "Apple event", "link": "https://news.example.com/event", "snippet": "New devices",
         "date": "2 hours ago", "source": "Example News"},
    ]
}


def run_main(argv, env=None, fetcher=None):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, env if env is not None else {}, clear=True):
        with redirect_stdout(out), redirect_stderr(err):
            code = ws.main(argv, fetcher=fetcher or ws.fetch)
    return code, out.getvalue(), err.getvalue()


class PayloadTests(unittest.TestCase):
    def test_since_maps_to_tbs(self):
        payload = ws.build_payload("q", since="w")
        self.assertEqual(payload["tbs"], "qdr:w")

    def test_no_since_omits_tbs(self):
        self.assertNotIn("tbs", ws.build_payload("q"))

    def test_num_is_capped_at_100(self):
        self.assertEqual(ws.build_payload("q", num=500)["num"], 100)

    def test_optional_fields_only_when_given(self):
        payload = ws.build_payload("q", gl="it", hl="en", page=2)
        self.assertEqual((payload["gl"], payload["hl"], payload["page"]), ("it", "en", 2))
        self.assertNotIn("gl", ws.build_payload("q"))

    def test_endpoint_per_vertical(self):
        self.assertEqual(ws.endpoint("search"), "https://google.serper.dev/search")
        self.assertEqual(ws.endpoint("news"), "https://google.serper.dev/news")
        self.assertEqual(ws.endpoint("scholar"), "https://google.serper.dev/scholar")


class RenderTests(unittest.TestCase):
    def test_render_search_lists_organic_with_date_and_extras(self):
        text = ws.render(SAMPLE_SEARCH, "search")
        self.assertIn("1. Apple", text)
        self.assertIn("https://www.apple.com/", text)
        self.assertIn("Aug 20, 2026", text)
        self.assertIn("Answer box: Cupertino", text)
        self.assertIn("Knowledge graph: Apple", text)
        self.assertIn("Who founded Apple?", text)
        self.assertIn("apple stock", text)

    def test_render_news_uses_news_key(self):
        text = ws.render(SAMPLE_NEWS, "news")
        self.assertIn("Apple event", text)
        self.assertIn("Example News", text)
        self.assertIn("2 hours ago", text)

    def test_render_empty_says_no_results(self):
        self.assertIn("No results", ws.render({"organic": []}, "search"))


class MainTests(unittest.TestCase):
    def test_missing_key_exits_2_with_setup_line(self):
        code, out, err = run_main(["apple"], env={})
        self.assertEqual(code, ws.EXIT_NO_KEY)
        self.assertIn("SERPER_API_KEY", err)
        self.assertEqual(out, "")

    def test_fetcher_error_exits_1(self):
        def boom(url, payload, key, timeout):
            raise ws.FetchError("HTTP 429 Too Many Requests")
        code, out, err = run_main(["apple"], env={"SERPER_API_KEY": "k"}, fetcher=boom)
        self.assertEqual(code, ws.EXIT_ERROR)
        self.assertIn("429", err)

    def test_success_renders_text_and_passes_payload(self):
        seen = {}
        def ok(url, payload, key, timeout):
            seen.update(url=url, payload=payload, key=key, timeout=timeout)
            return SAMPLE_SEARCH
        code, out, err = run_main(["apple inc", "--since", "m", "--gl", "it"],
                                  env={"SERPER_API_KEY": "k"}, fetcher=ok)
        self.assertEqual(code, ws.EXIT_OK)
        self.assertEqual(seen["url"], "https://google.serper.dev/search")
        self.assertEqual(seen["payload"]["q"], "apple inc")
        self.assertEqual(seen["payload"]["tbs"], "qdr:m")
        self.assertEqual(seen["payload"]["gl"], "it")
        self.assertEqual(seen["key"], "k")
        self.assertIn("1. Apple", out)

    def test_json_flag_prints_raw_response(self):
        code, out, err = run_main(["apple", "--json"], env={"SERPER_API_KEY": "k"},
                                  fetcher=lambda *a: SAMPLE_SEARCH)
        self.assertEqual(code, ws.EXIT_OK)
        self.assertEqual(json.loads(out)["organic"][0]["link"], "https://www.apple.com/")

    def test_num_above_10_notes_credit_cost_on_stderr(self):
        code, out, err = run_main(["apple", "--num", "30"], env={"SERPER_API_KEY": "k"},
                                  fetcher=lambda *a: SAMPLE_SEARCH)
        self.assertEqual(code, ws.EXIT_OK)
        self.assertIn("2 credits", err)

    def test_news_vertical_hits_news_endpoint(self):
        seen = {}
        def ok(url, payload, key, timeout):
            seen["url"] = url
            return SAMPLE_NEWS
        code, out, err = run_main(["apple", "--vertical", "news"], env={"SERPER_API_KEY": "k"},
                                  fetcher=ok)
        self.assertEqual(seen["url"], "https://google.serper.dev/news")
        self.assertIn("Apple event", out)


if __name__ == "__main__":
    unittest.main()


class KeyResolutionTests(unittest.TestCase):
    """The key may come from the environment or from the file the research lead
    writes when the user pastes one in chat. Every case uses a temp path: a test
    that touched the real ~/.serper_key could overwrite a working key."""

    def setUp(self):
        self.tmp = Path(__file__).parent / "_tmp_serper_key"
        self.addCleanup(lambda: self.tmp.exists() and self.tmp.unlink())

    def test_env_wins_over_file(self):
        self.tmp.write_text("from-file\n", encoding="utf-8")
        key, source = ws.resolve_key(env={"SERPER_API_KEY": "from-env"}, key_file=self.tmp)
        self.assertEqual((key, source), ("from-env", "env"))

    def test_file_used_when_env_empty(self):
        self.tmp.write_text("  from-file \n", encoding="utf-8")
        key, source = ws.resolve_key(env={}, key_file=self.tmp)
        self.assertEqual(key, "from-file")
        self.assertEqual(source, str(self.tmp))

    def test_no_key_anywhere(self):
        self.assertEqual(ws.resolve_key(env={}, key_file=self.tmp / "missing"), (None, None))

    def test_empty_file_is_no_key(self):
        self.tmp.write_text("\n", encoding="utf-8")
        self.assertEqual(ws.resolve_key(env={}, key_file=self.tmp), (None, None))

    def test_blank_env_var_falls_through_to_file(self):
        self.tmp.write_text("from-file", encoding="utf-8")
        key, _ = ws.resolve_key(env={"SERPER_API_KEY": "   "}, key_file=self.tmp)
        self.assertEqual(key, "from-file")

    def test_save_key_writes_stripped_value(self):
        ws.save_key("  abc123  ", key_file=self.tmp)
        self.assertEqual(self.tmp.read_text(encoding="utf-8"), "abc123\n")
        self.assertEqual(ws.resolve_key(env={}, key_file=self.tmp)[0], "abc123")

    def test_mask_shows_only_the_last_four(self):
        self.assertEqual(ws.mask("0123456789abcdef"), "************cdef")
        self.assertNotIn("0123", ws.mask("0123456789abcdef"))
        self.assertEqual(ws.mask("abc"), "****")


class KeyCliTests(unittest.TestCase):
    def test_check_key_reports_availability_without_fetching(self):
        def never(*a):
            raise AssertionError("--check-key must make no network call")
        code, out, err = run_main(["--check-key"], env={"SERPER_API_KEY": "k"}, fetcher=never)
        self.assertEqual(code, ws.EXIT_OK)
        self.assertIn("key available", out)

    def test_check_key_without_key_exits_2_with_setup_line(self):
        with mock.patch.object(ws, "KEY_FILE", Path(__file__).parent / "_absent_key"):
            code, out, err = run_main(["--check-key"], env={})
        self.assertEqual(code, ws.EXIT_NO_KEY)
        self.assertIn("serper.dev", err)

    def test_set_key_saves_from_stdin_and_masks_the_echo(self):
        tmp = Path(__file__).parent / "_tmp_cli_key"
        self.addCleanup(lambda: tmp.exists() and tmp.unlink())
        with mock.patch.object(ws, "KEY_FILE", tmp):
            out = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True):
                with redirect_stdout(out):
                    code = ws.main(["--set-key"], stdin=io.StringIO(" secret-key-1234 \n"))
        self.assertEqual(code, ws.EXIT_OK)
        self.assertEqual(tmp.read_text(encoding="utf-8"), "secret-key-1234\n")
        self.assertNotIn("secret-key", out.getvalue())
        self.assertIn("1234", out.getvalue())

    def test_set_key_with_empty_stdin_exits_2(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = ws.main(["--set-key"], stdin=io.StringIO("   \n"))
        self.assertEqual(code, ws.EXIT_NO_KEY)
        self.assertIn("No key on stdin", err.getvalue())

    def test_search_uses_the_key_file_when_env_is_empty(self):
        tmp = Path(__file__).parent / "_tmp_search_key"
        tmp.write_text("file-key\n", encoding="utf-8")
        self.addCleanup(lambda: tmp.exists() and tmp.unlink())
        seen = {}
        def ok(url, payload, key, timeout):
            seen["key"] = key
            return SAMPLE_SEARCH
        with mock.patch.object(ws, "KEY_FILE", tmp):
            code, out, err = run_main(["apple"], env={}, fetcher=ok)
        self.assertEqual(code, ws.EXIT_OK)
        self.assertEqual(seen["key"], "file-key")

    def test_missing_query_exits_1_not_2(self):
        code, out, err = run_main([], env={"SERPER_API_KEY": "k"})
        self.assertEqual(code, ws.EXIT_ERROR)
        self.assertIn("No query", err)
