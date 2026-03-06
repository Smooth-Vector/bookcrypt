"""Tests for bookcrypt.indexer."""

import pytest

from bookcrypt.indexer import DEFAULT_PAGE_SIZE, build_index, paginate


# ---------------------------------------------------------------------------
# paginate
# ---------------------------------------------------------------------------

class TestPaginate:
    def test_single_page(self):
        words = ["a", "b", "c"]
        pages = paginate(words, page_size=10)
        assert pages == [["a", "b", "c"]]

    def test_exact_multiple(self):
        words = list("abcdef")
        pages = paginate(words, page_size=2)
        assert pages == [["a", "b"], ["c", "d"], ["e", "f"]]

    def test_remainder_on_last_page(self):
        words = list("abcde")
        pages = paginate(words, page_size=2)
        assert pages == [["a", "b"], ["c", "d"], ["e"]]

    def test_empty_words(self):
        assert paginate([], page_size=250) == []

    def test_invalid_page_size(self):
        with pytest.raises(ValueError):
            paginate(["a"], page_size=0)

    def test_default_page_size(self):
        words = ["word"] * 500
        pages = paginate(words)
        assert len(pages) == 500 // DEFAULT_PAGE_SIZE
        assert all(len(p) == DEFAULT_PAGE_SIZE for p in pages)

    def test_page_count(self):
        words = ["w"] * 1000
        pages = paginate(words, page_size=250)
        assert len(pages) == 4


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------

class TestBuildIndex:
    def test_basic_index(self):
        pages = [["the", "whale", "swam"], ["the", "sea", "was", "dark"]]
        index = build_index(pages)
        assert index["the"] == [1, 2]
        assert index["whale"] == [1]
        assert index["sea"] == [2]

    def test_page_numbers_are_one_based(self):
        pages = [["hello"], ["world"]]
        index = build_index(pages)
        assert index["hello"] == [1]
        assert index["world"] == [2]

    def test_word_appears_once_per_page(self):
        # "whale" appears multiple times on page 1 — should only index once
        pages = [["whale", "whale", "whale"]]
        index = build_index(pages)
        assert index["whale"] == [1]

    def test_page_numbers_sorted(self):
        pages = [["a"], ["b"], ["a"], ["c"], ["a"]]
        index = build_index(pages)
        assert index["a"] == [1, 3, 5]

    def test_empty_pages(self):
        assert build_index([]) == {}

    def test_returns_dict(self):
        assert isinstance(build_index([["word"]]), dict)

    def test_all_words_indexed(self):
        pages = [["foo", "bar"], ["baz"]]
        index = build_index(pages)
        assert set(index.keys()) == {"foo", "bar", "baz"}


# ---------------------------------------------------------------------------
# Integration: paginate + build_index
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_word_lookup_across_pages(self):
        # 500 words: "whale" at position 0 (page 1) and 499 (page 2)
        words = ["filler"] * 500
        words[0] = "whale"
        words[499] = "whale"
        pages = paginate(words, page_size=250)
        index = build_index(pages)
        assert index["whale"] == [1, 2]

    def test_unique_word_single_page(self):
        words = ["filler"] * 249 + ["ahab"]
        pages = paginate(words, page_size=250)
        index = build_index(pages)
        assert index["ahab"] == [1]
