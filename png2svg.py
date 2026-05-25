import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import vtracer
import subprocess
import argparse

from config import CONFIG

SVG_NS = "http://www.w3.org/2000/svg"
UPM = CONFIG.upm
ET.register_namespace("", SVG_NS)


def normalize_svg_root(svg_path: str) -> str:
    tree = ET.parse(svg_path)
    root = tree.getroot()

    handle, temp_path = tempfile.mkstemp(suffix=".svg")
    os.close(handle)

    tree.write(temp_path, encoding="utf-8", xml_declaration=False)
    return temp_path


def wrap_png_to_svg(png_path, svg_output_path, width=150, height=150, target_upm=UPM):
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as temp_file:
        temp_svg_path = temp_file.name

    try:
        vtracer.convert_image_to_svg_py(str(png_path), str(temp_svg_path))

        tree = ET.parse(temp_svg_path)
        root = tree.getroot()
        namespace = root.tag[1:].split("}", 1)[0] if root.tag.startswith("{") else ""

        view_box = root.attrib.get("viewBox")
        if view_box:
            _, _, source_width, source_height = map(float, view_box.split())
        else:
            source_width = float(root.attrib.get("width", width))
            source_height = float(root.attrib.get("height", height))

        scale = target_upm / source_height

        children = list(root)

        wrapper_tag = f"{{{namespace}}}g" if namespace else "g"
        wrapper = ET.Element(
            wrapper_tag,
            {
                "transform": f"scale({scale}) translate(0,-{source_height})",
            },
        )

        for child in children:
            root.remove(child)
            wrapper.append(child)

        root.append(wrapper)
        root.set("viewBox", f"0 -{target_upm} {target_upm} {target_upm}")
        root.set("width", str(target_upm))
        root.set("height", str(target_upm))

        ET.indent(tree, space="  ")
        tree.write(temp_svg_path, encoding="utf-8", xml_declaration=True)
        normalized_svg_path = normalize_svg_root(temp_svg_path)
        try:
            subprocess.run(
                ["./svgcleaner", normalized_svg_path, svg_output_path], check=True
            )
        finally:
            if os.path.exists(normalized_svg_path):
                os.remove(normalized_svg_path)
    finally:
        if os.path.exists(temp_svg_path):
            os.remove(temp_svg_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PNG glyphs to normalized SVGs.")
    parser.add_argument(
        "--png_folder",
        dest="png_folder",
        default="glyphs",
        help="Input folder containing PNG glyphs (default: glyphs)",
    )
    parser.add_argument(
        "--svg_output",
        dest="svg_output",
        default="svg_glyphs",
        help="Output folder for generated SVGs (default: svg_glyphs)",
    )
    args = parser.parse_args()

    png_directory = Path(args.png_folder)
    svg_output_directory = Path(args.svg_output)

    svg_output_directory.mkdir(parents=True, exist_ok=True)

    for png_path in sorted(png_directory.glob("*.png")):
        filename = png_path.name
        new_file_name = filename.replace("_alpha", "").rsplit(".", 1)[0] + ".svg"
        svg_output_path = svg_output_directory / new_file_name
        wrap_png_to_svg(png_path, svg_output_path)
        print(f"Converted {filename} to SVG format.")


if __name__ == "__main__":
    main()
