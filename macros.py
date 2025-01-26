import uuid
from pathlib import Path
import re
from textwrap import dedent
from isd.isd import get_default_settings_yaml, get_default_settings


def value_str(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return '"' + value + '"'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, list):
        elements = [value_str(v) for v in value]
        return "[" + ", ".join(elements) + "]"
    return value


def extract_timestamps(file) -> list[str]:
    return [
        m.group("timestamp")
        for m in re.finditer(
            r'^\[(?P<timestamp>[\d.]+), "m",', Path(file).read_text(), re.MULTILINE
        )
    ]


def format_timestamps(timestamps: list[str]) -> list[str]:
    return [f"npt:{t}" for t in timestamps]


def define_env(env):
    env.variables["timestamps"] = extract_timestamps(
        Path(env.project_dir) / "docs/assets/images/isd.cast"
    )
    env.variables["poster_markers"] = format_timestamps(env.variables["timestamps"])
    env.variables["default_settings"] = get_default_settings()
    env.variables["default_config_data"] = get_default_settings_yaml()

    @env.macro
    def config_block(number: int) -> str:
        block = env.variables.default_config_data.split("\n\n")[number]
        return "```yaml\n" + block + "\n```"

    @env.macro
    def render_shortcut(keys: str) -> str:
        return " or ".join(f"++{key}++" for key in keys.split(","))

    @env.macro
    def asciinema(file, **kwargs):
        html = ""
        opts = {
            "autoPlay": False,
            "controls": True,
            "loop": False,
            "pauseOnMarkers": True,
        }

        # Overwrite defaults with kwargs
        for key, value in kwargs.items():
            if key == "marker_names":
                opts["markers"] = [
                    [float(timestamp), name]
                    for timestamp, name in zip(env.variables.timestamps, value)
                ]
            else:
                opts[key] = value

        # Create an empty div that we will use for the player
        div_id = "asciinema-" + str(uuid.uuid4())
        div_style = "z-index: 1; position: relative;"
        html += '<div id="' + div_id + '" style="' + div_style + '"></div>'

        # if "poster_mark" in kwargs:
        #     opts["poster"] = f"'{marker_timestamps["poster_mark"]}'"

        # Define JS representing creating the player
        create_player_js = ""
        create_player_js += (
            "AsciinemaPlayer.create('"
            + file
            + "', document.getElementById('"
            + div_id
            + "'), {"
        )
        for key, value in opts.items():
            create_player_js += '"' + key + '": ' + value_str(value) + ","

        create_player_js += "});"

        # Create script tag that will perform cast by either registering for the DOM to
        # load or firing immediately if already loaded
        html += "<script>"
        html += "if (document.readyState === 'loading') {"
        html += "document.addEventListener('DOMContentLoaded', function() {"
        html += create_player_js
        html += "});"
        html += "} else {"
        html += create_player_js
        html += "}"
        html += "</script>"

        return html
