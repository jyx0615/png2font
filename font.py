import fontforge
import os
import re
import argparse

from config import CONFIG


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("svg_folder", nargs="?", default="svg_glyphs/")
    parser.add_argument("--fontname")
    parser.add_argument("--fullname")
    parser.add_argument("--familyname")
    return parser.parse_args()


def resolve_config(args: argparse.Namespace) -> tuple[str, str, str, str]:
    fontname = args.fontname or CONFIG.fontname
    fullname = args.fullname or CONFIG.fullname
    familyname = args.familyname or CONFIG.familyname
    return args.svg_folder, fontname, fullname, familyname


# 建立新的字型專案
ARGS = parse_args()
SVG_FOLDER, fontname, fullname, familyname = resolve_config(ARGS)

font = fontforge.font()
font.encoding = "UnicodeFull"
font.fontname = fontname
font.fullname = fullname
font.familyname = familyname
svg_folder = SVG_FOLDER  # 存放 SVG 字圖的資料夾


def svg_filename_to_codepoint(filename: str) -> int:
    stem = filename.rsplit(".", 1)[0]
    prefix = stem.split("_", 1)[0]

    if len(prefix) == 1:
        return ord(prefix)

    if re.fullmatch(r"u[0-9a-fA-F]{4,6}", prefix):
        return int(prefix[1:], 16)

    if re.fullmatch(r"[0-9a-fA-F]{4,6}", prefix):
        return int(prefix, 16)

    raise ValueError(f"Cannot infer a Unicode code point from {filename!r}.")


def import_glyphs_from_svg(folder):

    for filename in os.listdir(folder):
        if filename.endswith(".svg"):
            # resize the svg to fit the em square (1000x1000)
            svg_path = os.path.join(folder, filename)
            char_code = svg_filename_to_codepoint(filename)
            glyph = font.createChar(char_code)
            # if char_code >= ord("a") and char_code <= ord("z"):
            #     glyph.glyphname = f"{filename[0]}_lower"
            glyph.glyphname = f"{filename.rsplit('.', 1)[0]}"
            glyph.importOutlines(svg_path)

            xmin, ymin, xmax, ymax = glyph.boundingBox()
            width = xmax - xmin
            height = ymax - ymin

            if width > 0 and height > 0:
                # png2svg.py already scaled every SVG so that the PNG canvas
                # height maps to UPM — all glyphs share the same vertical
                # reference.  Do NOT re-scale here; that would blow up short
                # glyphs (=, –, …) to enormous widths.
                # Just shift the glyph so its left ink edge starts at x = 0.
                glyph.transform((1, 0, 0, 1, -xmin, 0))

            if char_code == 32:
                glyph.width = CONFIG.space_width
            else:
                # Advance width = actual ink width (no sidebearing).
                xmin2, _, xmax2, _ = glyph.boundingBox()
                glyph.width = max(1, round(xmax2 - xmin2))
            print(
                f"Successfully imported {filename} to Unicode {char_code} {chr(char_code)}"
            )

    font.generate(f"{font.fontname}.ttf")


def main() -> None:
    import_glyphs_from_svg(svg_folder)


if __name__ == "__main__":
    main()
