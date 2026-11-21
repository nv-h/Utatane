"""Check a generated Regular/Bold pair against the Utatane width policy.

Run from the repository root with FontTools installed:
    python -m analysis.check_width_policy dist/Utatane-Regular.ttf dist/Utatane-Bold.ttf
"""

import argparse
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont

from width_policy import expected_cells


def read_advances(path):
    with TTFont(path) as font:
        upm = font["head"].unitsPerEm
        if upm % 2:
            raise ValueError(f"{path}: expected an even unitsPerEm, got {upm}")
        metrics = font["hmtx"].metrics
        return upm // 2, {
            codepoint: metrics[glyph][0] for codepoint, glyph in font.getBestCmap().items()
        }


def describe(codepoint):
    return f"U+{codepoint:04X} {unicodedata.name(chr(codepoint), '<unnamed>')}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("regular", type=Path)
    parser.add_argument("bold", type=Path)
    args = parser.parse_args()

    reference_path = Path(__file__).resolve().parents[1] / "sourceFonts/mplus-1m-regular.ttf"
    mplus_half, mplus_advances = read_advances(reference_path)
    mplus_cells = {cp: width // mplus_half for cp, width in mplus_advances.items()
                   if width in (mplus_half, 2 * mplus_half)}

    regular_half, regular = read_advances(args.regular)
    bold_half, bold = read_advances(args.bold)
    problems = []
    for path, half, advances in [(args.regular, regular_half, regular), (args.bold, bold_half, bold)]:
        for codepoint, actual in sorted(advances.items()):
            cells = expected_cells(codepoint, mplus_cells)
            if actual not in (0, half, 2 * half) or (cells is not None and actual != cells * half):
                expected = str(cells * half) if cells is not None else f"0, {half}, or {2 * half}"
                problems.append(f"{path.name}: {describe(codepoint)} expected {expected}, got {actual}")

    for codepoint in sorted(regular.keys() | bold.keys()):
        regular_width, bold_width = regular.get(codepoint), bold.get(codepoint)
        if regular_width is None or bold_width is None:
            problems.append(f"{describe(codepoint)} coverage: Regular {regular_width}, Bold {bold_width}")
        elif regular_width * bold_half != bold_width * regular_half:
            problems.append(f"{describe(codepoint)} advance: Regular {regular_width}, Bold {bold_width}")

    if problems:
        print("\n".join(problems))
        print(f"{len(problems)} width or coverage discrepancies")
        return 1
    print(f"{len(regular):,} codepoints per weight pass the width and coverage checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
