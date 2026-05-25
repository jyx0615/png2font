import fontforge
import os
import re
import argparse

from config import CONFIG

# 建立新的字型專案
font = fontforge.font()
font.fontname = CONFIG.fontname
font.fullname = CONFIG.fullname
font.familyname = CONFIG.familyname
svg_folder = "svg_glyphs/"  # 存放 SVG 字圖的資料夾
VERTICAL_RAISE = 120
MONOSPACE_WIDTH = CONFIG.advance_width


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
                scale = min(CONFIG.upm / width, CONFIG.upm / height)
                glyph.transform(
                    (
                        scale,
                        0,
                        0,
                        scale,
                        -xmin * scale,
                        (-ymin * scale) + VERTICAL_RAISE,
                    )
                )
            glyph.width = MONOSPACE_WIDTH
            print(
                f"Successfully imported {filename} to Unicode {char_code} {chr(char_code)}"
            )

    font.generate(f"{font.fontname}.ttf")


def main() -> None:
    import_glyphs_from_svg(svg_folder)


if __name__ == "__main__":
    main()
