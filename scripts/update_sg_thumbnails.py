"""Rewrite sport_global channel thumbnails to use local /israel_tv/logos/ paths."""

import re
from pathlib import Path

CHANNELS_PY = Path(__file__).parent.parent / "custom_components" / "israel_tv" / "channels.py"
LOGOS_DIR = Path(__file__).parent.parent / "custom_components" / "israel_tv" / "logos"
LOCAL_BASE = "/israel_tv/logos/{}.png"

content = CHANNELS_PY.read_text(encoding="utf-8")

# Find all sg_ channel blocks and rewrite their thumbnail line
def replace_thumbnail(m):
    block = m.group(0)
    # Extract channel id
    id_match = re.search(r'id="(sg_[^"]+)"', block)
    if not id_match:
        return block
    ch_id = id_match.group(1)
    local_path = LOGOS_DIR / f"{ch_id}.png"

    if local_path.exists():
        new_thumb = f'thumbnail="{LOCAL_BASE.format(ch_id)}"'
    else:
        new_thumb = None  # remove thumbnail

    # Replace existing thumbnail= line or add/remove it
    if re.search(r'thumbnail=', block):
        if new_thumb:
            block = re.sub(r'thumbnail="[^"]*"', new_thumb, block)
        else:
            # Remove thumbnail line entirely
            block = re.sub(r'\s+thumbnail="[^"]*",?\n', '\n', block)
    return block

# Match each sg_ Channel() block
pattern = re.compile(
    r'Channel\(\s+id="sg_[^"]+".+?\)',
    re.DOTALL
)

new_content = pattern.sub(replace_thumbnail, content)
CHANNELS_PY.write_text(new_content, encoding="utf-8")
print("Done - thumbnails updated to local paths")
