import unittest

from agents.research_agent import (
    _normalize_serper,
    _normalize_tavily,
    build_query,
    format_bullets,
)


class ResearchAgentTests(unittest.TestCase):
    def test_build_query_with_niche(self) -> None:
        query = build_query("personal branding", "creator economy")
        self.assertEqual(
            query,
            "Trending topics and recent facts about personal branding in creator economy",
        )

    def test_build_query_without_niche(self) -> None:
        query = build_query("personal branding", None)
        self.assertEqual(
            query,
            "Trending topics and recent facts about personal branding",
        )

    def test_normalize_tavily_keeps_titles_snippets_and_sources(self) -> None:
        bullets, sources = _normalize_tavily(
            {
                "results": [
                    {
                        "title": "Trend A",
                        "content": "Snippet A",
                        "url": "https://example.com/a",
                    },
                    {
                        "title": "",
                        "content": "Snippet B",
                        "url": "https://example.com/b",
                    },
                ]
            },
            limit=5,
        )
        self.assertEqual(bullets, ["Trend A: Snippet A", "Snippet B"])
        self.assertEqual(
            sources,
            ["https://example.com/a", "https://example.com/b"],
        )

    def test_normalize_serper_respects_limit(self) -> None:
        bullets, sources = _normalize_serper(
            {
                "organic": [
                    {
                        "title": "Trend A",
                        "snippet": "Snippet A",
                        "link": "https://example.com/a",
                    },
                    {
                        "title": "Trend B",
                        "snippet": "Snippet B",
                        "link": "https://example.com/b",
                    },
                ]
            },
            limit=1,
        )
        self.assertEqual(bullets, ["Trend A: Snippet A"])
        self.assertEqual(sources, ["https://example.com/a"])

    def test_format_bullets_returns_markdown_list(self) -> None:
        formatted = format_bullets(["one", "two"])
        self.assertEqual(formatted, "- one\n- two")


if __name__ == "__main__":
    unittest.main()
