from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


@dataclass(frozen=True)
class FontConfig:
    upm: int = 1000
    advance_width: int = 600
    space_width: int = 250
    fontname: str = "MyCustomFont"
    fullname: str = "My Custom Font"
    familyname: str = "My Family"


def load_config(config_path: str | Path = "config.toml") -> FontConfig:
    path = Path(config_path)
    if not path.exists():
        return FontConfig()

    with path.open("rb") as config_file:
        data = tomllib.load(config_file)

    font_settings = data.get("font", {})
    return FontConfig(
        upm=int(font_settings.get("upm", 1000)),
        advance_width=int(font_settings.get("advance_width", 600)),
        space_width=int(font_settings.get("space_width", 250)),
        fontname=str(font_settings.get("fontname", "MyCustomFont")),
        fullname=str(font_settings.get("fullname", "My Custom Font")),
        familyname=str(font_settings.get("familyname", "My Family")),
    )


CONFIG = load_config()
