"""Parser registry — selects the correct parser for a given G-code file.

Parsers are tried in priority order.  The first parser whose can_parse()
returns True is used.  GenericGcodeParser is always last and always matches,
making it the guaranteed fallback.

Adding support for a new slicer requires only:
  1. A new file in app/parsers/
  2. A new entry in _PARSERS before GenericGcodeParser
"""

from app.parsers.base import BaseParser, PrintEstimate
from app.parsers.creality import CrealityGcodeParser
from app.parsers.generic import GenericGcodeParser

_PARSERS: list[BaseParser] = [
    CrealityGcodeParser(),
    GenericGcodeParser(),  # must remain last
]


def parse_gcode(text: str) -> PrintEstimate:
    """Return a normalized PrintEstimate from raw G-code header text.

    Raises:
        ValueError: If no parser can extract the required fields.
    """
    for parser in _PARSERS:
        if parser.can_parse(text):
            return parser.extract(text)

    # Unreachable while GenericGcodeParser is in the list, but kept for safety.
    raise ValueError("Unable to detect slicer format — no matching parser found")
