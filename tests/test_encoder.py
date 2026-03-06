"""Tests for bookcrypt.encoder."""

import pytest

from bookcrypt.encoder import build_position_index, encode, format_encoded
from bookcrypt.indexer import paginate
from bookcrypt.parser import extract_words


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_pages() -> list[list[str]]:
    """Three small pages for unit tests."""
    return [
        ["call", "me", "ishmael", "some", "years", "ago"],
        ["the", "whale", "swam", "through", "dark", "waters"],
        ["call", "me", "captain", "ahab", "whale", "hunter"],
    ]


@pytest.fixture()
def position_index(simple_pages: list[list[str]]) -> dict[str, list[tuple[int, int]]]:
    return build_position_index(simple_pages)


# ---------------------------------------------------------------------------
# build_position_index
# ---------------------------------------------------------------------------

class TestBuildPositionIndex:
    def test_returns_dict(self, simple_pages):
        assert isinstance(build_position_index(simple_pages), dict)

    def test_coordinates_are_one_based(self, position_index):
        # "call" is first word on page 1
        assert (1, 1) in position_index["call"]

    def test_all_occurrences_recorded(self, position_index):
        # "call" appears on page 1 pos 1 and page 3 pos 1
        assert position_index["call"] == [(1, 1), (3, 1)]

    def test_single_occurrence_word(self, position_index):
        assert position_index["ishmael"] == [(1, 3)]

    def test_position_within_page(self, position_index):
        # "whale" is 2nd word on page 2
        assert (2, 2) in position_index["whale"]

    def test_empty_pages(self):
        assert build_position_index([]) == {}

    def test_every_word_indexed(self, simple_pages, position_index):
        all_words = {w for page in simple_pages for w in page}
        assert set(position_index.keys()) == all_words


# ---------------------------------------------------------------------------
# encode
# ---------------------------------------------------------------------------

class TestEncode:
    def test_single_word(self, position_index):
        assert encode("ishmael", position_index) == [(1, 3)]

    def test_multiple_words(self, position_index):
        result = encode("call me ishmael", position_index)
        assert result == [(1, 1), (1, 2), (1, 3)]

    def test_uses_first_occurrence(self, position_index):
        # "call" appears on pages 1 and 3; first occurrence is (1, 1)
        result = encode("call", position_index)
        assert result == [(1, 1)]

    def test_repeated_word_uses_successive_occurrences(self, position_index):
        # "call" is at (1,1) and (3,1); two uses should consume both in order
        result = encode("call call", position_index)
        assert result == [(1, 1), (3, 1)]

    def test_exhausted_word_raises(self, position_index):
        # "ishmael" appears only once
        with pytest.raises(ValueError, match="exhausted"):
            encode("ishmael ishmael", position_index)

    def test_does_not_mutate_index(self, position_index):
        original = {w: list(coords) for w, coords in position_index.items()}
        encode("call me ishmael", position_index)
        assert position_index == original

    def test_case_insensitive(self, position_index):
        assert encode("ISHMAEL", position_index) == encode("ishmael", position_index)

    def test_punctuation_ignored(self, position_index):
        assert encode("call me, ishmael!", position_index) == [(1, 1), (1, 2), (1, 3)]

    def test_empty_sentence(self, position_index):
        assert encode("", position_index) == []

    def test_missing_word_raises(self, position_index):
        with pytest.raises(ValueError, match="not found in book"):
            encode("supercalifragilistic", position_index)

    def test_multiple_missing_words_reported(self, position_index):
        with pytest.raises(ValueError, match="foo") as exc_info:
            encode("foo bar", position_index)
        assert "bar" in str(exc_info.value)

    def test_returns_list_of_tuples(self, position_index):
        result = encode("the whale", position_index)
        assert isinstance(result, list)
        assert all(isinstance(c, tuple) and len(c) == 2 for c in result)


# ---------------------------------------------------------------------------
# format_encoded
# ---------------------------------------------------------------------------

class TestFormatEncoded:
    def test_single_coord(self):
        assert format_encoded([(4, 34)]) == "4 34"

    def test_multiple_coords(self):
        assert format_encoded([(4, 34), (7, 12), (1, 5)]) == "4 34 7 12 1 5"

    def test_empty(self):
        assert format_encoded([]) == ""


# ---------------------------------------------------------------------------
# Integration: real book
# ---------------------------------------------------------------------------

class TestIntegrationRealBook:
    @pytest.fixture(scope="class")
    def book_index(self):
        words = extract_words("moby_dick.epub")
        pages = paginate(words, page_size=250)
        return build_position_index(pages)

    def test_encodes_opening_words(self, book_index):
        coords = encode("call me ishmael", book_index)
        assert len(coords) == 3
        assert all(isinstance(p, int) and isinstance(pos, int) for p, pos in coords)

    def test_format_output(self, book_index):
        coords = encode("the whale", book_index)
        encoded = format_encoded(coords)
        # "the whale" -> "p1 pos1 p2 pos2"
        parts = encoded.split()
        assert len(parts) == 4
        assert all(int(p) >= 1 for p in parts)

    def test_unknown_word_raises(self, book_index):
        with pytest.raises(ValueError):
            encode("supercalifragilistic", book_index)
