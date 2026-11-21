"""Default horizontal advances for Utatane's 1:2 grid, in cells."""

import unicodedata

TERMINAL_ONE_CELL = frozenset(range(0x2500, 0x2580)) | {
    0x2015,  # HORIZONTAL BAR
    0x2026,  # HORIZONTAL ELLIPSIS
    0x2591, 0x2592, 0x2593,  # Shade characters
}

SPACE_CELLS = {0x2002: 1, 0x2003: 2}  # EN SPACE, EM SPACE


def expected_cells(codepoint, mplus_cells):
    """Return the expected advance, or None when the existing advance is used."""
    character = chr(codepoint)
    category = unicodedata.category(character)
    if category in {"Mn", "Me"}:
        return 0
    if category.startswith("C"):
        return None
    if codepoint in TERMINAL_ONE_CELL:
        return 1
    if codepoint in SPACE_CELLS:
        return SPACE_CELLS[codepoint]

    east_asian_width = unicodedata.east_asian_width(character)
    if east_asian_width in {"F", "W"}:
        return 2
    if east_asian_width in {"H", "Na"}:
        return 1
    if codepoint in mplus_cells:
        return mplus_cells[codepoint]
    if category.startswith("L") and unicodedata.name(character, "").startswith(
        ("LATIN ", "GREEK ", "CYRILLIC ")
    ):
        return 1
    return None
