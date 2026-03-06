"""Command-line interface for bookcrypt."""

import argparse
import sys

from bookcrypt.encoder import build_position_index, encode, format_encoded
from bookcrypt.indexer import paginate
from bookcrypt.parser import extract_words

DEFAULT_EPUB = "moby_dick.epub"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bookcrypt",
        description="Encode a message using the Moby Dick book cipher.",
    )
    parser.add_argument("message", help="The sentence to encode.")
    parser.add_argument(
        "--epub",
        default=DEFAULT_EPUB,
        metavar="PATH",
        help=f"Path to the EPUB file (default: {DEFAULT_EPUB})",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=250,
        metavar="N",
        help="Words per virtual page (default: 250)",
    )

    args = parser.parse_args()

    try:
        words = extract_words(args.epub)
    except FileNotFoundError:
        print(f"error: EPUB not found: {args.epub}", file=sys.stderr)
        sys.exit(1)

    pages = paginate(words, page_size=args.page_size)
    index = build_position_index(pages)

    try:
        coords = encode(args.message, index)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    print(format_encoded(coords))


if __name__ == "__main__":
    main()
