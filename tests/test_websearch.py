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
SCRIPT = REPO_ROOT / "plugins" / "research" / "scripts" / "websearch.py"


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
