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

    Each word in the sentence is mapped to its next unused occurrence in the
    book as a ``(page, position)`` coordinate. Each coordinate is consumed
    exactly once — repeated words in the sentence draw from successive
    occurrences in the book. Words are normalised the same way as the parser
    (lowercase, keeping apostrophes and hyphens).

    Args:
        sentence: Plain-text sentence to encode.
        position_index: Index built by ``build_position_index``. This mapping
            is not mutated; a local iterator is used per call.

    Returns:
        List of ``(page, position)`` tuples, one per word token in the sentence.

    Raises:
        ValueError: If any word in the sentence does not appear in the book, or
            if a word has been used more times than it appears in the book.

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

    # Per-call iterator over each word's occurrences — does not mutate the index
    iterators: dict[str, int] = {}
    result: list[Coordinate] = []
    errors: list[str] = []

    for word in words:
        if word not in position_index:
            errors.append(f"'{word}' not found in book")
            continue

        idx = iterators.get(word, 0)
        occurrences = position_index[word]

        if idx >= len(occurrences):
            errors.append(f"'{word}' exhausted (appears {len(occurrences)} time(s) in book)")
            continue

        result.append(occurrences[idx])
        iterators[word] = idx + 1

    if errors:
        raise ValueError(f"Encoding failed: {'; '.join(errors)}")

    return result


def format_encoded(coords: list[Coordinate]) -> str:
    """Format a list of coordinates as a space-separated string.

    Each coordinate is rendered as ``page position`` separated by a space.

    Args:
        coords: List of ``(page, position)`` tuples as returned by ``encode``.

    Returns:
        Human-readable encoding string, e.g. ``"4 34 7 12 1 5"``.
    """
    return " ".join(f"{page} {pos}" for page, pos in coords)

def decode(encoded: str, pages: list[list[str]]) -> str:
    """Decode an encoded coordinate string back into a sentence.

    Parses pairs of numbers from ``encoded`` and looks up the word at each
    ``(page, position)`` coordinate in ``pages``.

    Args:
        encoded: Space-separated coordinate string as produced by
            ``format_encoded``, e.g. ``"15 76 6 215 18 44"``.
        pages: List of pages as returned by ``paginate``.

    Returns:
        Decoded sentence as a space-separated string of words.

    Raises:
        ValueError: If ``encoded`` contains an odd number of tokens, or if any
            coordinate is out of range for the given pages.

    Example::

        pages = paginate(extract_words("moby_dick.epub"))
        index = build_position_index(pages)
        coords = encode("call me ishmael", index)
        sentence = decode(format_encoded(coords), pages)
        assert sentence == "call me ishmael"
    """
    tokens = encoded.split()
    if len(tokens) % 2 != 0:
        raise ValueError(f"Encoded string must contain an even number of tokens, got {len(tokens)}")

    words: list[str] = []
    for i in range(0, len(tokens), 2):
        try:
            page = int(tokens[i])
            pos = int(tokens[i + 1])
        except ValueError:
            raise ValueError(f"Invalid coordinate at token {i}: '{tokens[i]} {tokens[i + 1]}'")

        if page < 1 or page > len(pages):
            raise ValueError(f"Page {page} out of range (book has {len(pages)} pages)")
        page_words = pages[page - 1]
        if pos < 1 or pos > len(page_words):
            raise ValueError(f"Position {pos} out of range on page {page} ({len(page_words)} words)")

        words.append(page_words[pos - 1])

    return " ".join(words)
