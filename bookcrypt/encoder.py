"""Encoder: book cipher encoding of sentences using page/position coordinates."""

from bookcrypt.parser import tokenize

# Type alias: (page_number, position_on_page), both 1-based
Coordinate = tuple[int, int]


def build_position_index(pages: list[list[str]]) -> dict[str, list[Coordinate]]:
    """Build a word-to-coordinates index from paginated content.

    Each word maps to every (page, position) location it occupies in the book.
    Both page number and position are 1-based.

    Args:
        pages: List of pages as returned by ``paginate``.

    Returns:
        Dictionary mapping each word to a list of ``(page, position)`` tuples
        in the order they appear in the book.

    Example::

        pages = paginate(extract_words("moby_dick.epub"))
        index = build_position_index(pages)
        print(index["whale"])  # [(3, 12), (3, 201), (4, 88), ...]
    """
    index: dict[str, list[Coordinate]] = {}
    for page_num, page_words in enumerate(pages, start=1):
        for pos, word in enumerate(page_words, start=1):
            index.setdefault(word, []).append((page_num, pos))
    return index


def encode(sentence: str, position_index: dict[str, list[Coordinate]]) -> list[Coordinate]:
    """Encode a sentence as a list of book coordinates.

    Each word in the sentence is mapped to its first occurrence in the book as
    a ``(page, position)`` coordinate. Words are normalised the same way as the
    parser (lowercase, keeping apostrophes and hyphens).

    Args:
        sentence: Plain-text sentence to encode.
        position_index: Index built by ``build_position_index``.

    Returns:
        List of ``(page, position)`` tuples, one per word token in the sentence.

    Raises:
        ValueError: If any word in the sentence does not appear in the book.

    Example::

        pages = paginate(extract_words("moby_dick.epub"))
        index = build_position_index(pages)
        coords = encode("call me ishmael", index)
        # e.g. [(1, 3), (1, 5), (1, 7)]
        print(" ".join(f"{p} {pos}" for p, pos in coords))
        # "1 3 1 5 1 7"
    """
    words = tokenize(sentence)
    if not words:
        return []

    result: list[Coordinate] = []
    missing: list[str] = []

    for word in words:
        if word not in position_index:
            missing.append(word)
        else:
            result.append(position_index[word][0])

    if missing:
        raise ValueError(f"Word(s) not found in book: {', '.join(repr(w) for w in missing)}")

    return result


def format_encoded(coords: list[Coordinate]) -> str:
    """Format a list of coordinates as a space-separated string.

    Each coordinate is rendered as ``page position`` with word boundaries
    separated by ``|``.

    Args:
        coords: List of ``(page, position)`` tuples as returned by ``encode``.

    Returns:
        Human-readable encoding string, e.g. ``"4 34|7 12|1 5"``.
    """
    return "|".join(f"{page} {pos}" for page, pos in coords)
