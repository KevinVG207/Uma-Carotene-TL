from fontTools.ttLib import TTFont
import util
import shutil
import os
import math
import re

def prepare_font():
    print("Loading font.")

    with util.MetaConnection() as (conn, cursor):
        cursor.execute("SELECT h FROM a WHERE n = 'font/dynamic01.otf'")
        row = cursor.fetchone()
    
    if not row:
        raise Exception("Font not found in meta db.")

    font_hash = row[0]
    
    font_path = util.MDB_FOLDER_EDITING + "font/dynamic01.otf"
    os.makedirs(os.path.dirname(font_path), exist_ok=True)

    shutil.copy(util.get_asset_path(font_hash), font_path)

    return TTFont(font_path)

# Set max width per category
MAX_WIDTHS = {
    "text_data/144.json": (14000, None, None),
}

def fix_newlines(text, width_data, font):
    text = text.replace("\r", "").replace("\n", "").replace("\\r", "").replace("\\n", "").strip()

    # text = re.sub(r"<.*?>", "", text)

    lines = split_text_into_lines(text, font, width_data)
    return lines

# def fix_newlines(font):
#     """Automatically add newlines to text that is too long.
#     Max width is defined per category.
#     """
#     print("Fixing newlines.")

#     # Load category data
#     for cat, width_data in MAX_WIDTHS.items():
#         cat_file = util.MDB_FOLDER_EDITING + f"text_data/{cat}.json"
#         if not os.path.exists(cat_file):
#             print(f"Skipping {cat}, file not found.")
#             continue
        
#         cat_data = util.load_json(cat_file)

#         for entry in cat_data:
#             entry['text'] = fix_newlines(entry['text'], width_data, font)
        
#         util.save_json(cat_file, cat_data)

def split_text_into_lines(text, font, width_data):
    """Split text into lines based on max width, using font."""
    max_width, max_lines, default_size = width_data

    lines = []
    cur_line = ""
    for word in text.split(" "):
        # Check if word fits on current line
        future_line = cur_line + " " + word if cur_line else word
        if get_text_width(future_line, font) > max_width:
            # Word doesn't fit
            lines.append(cur_line)
            cur_line = word
            continue

        # Word fits
        cur_line = future_line

    # Add last line
    lines.append(cur_line)

    out = ""
    # Check if we have too many lines
    if max_lines and len(lines) > max_lines:
        # Scale the text down
        scale_factor = max_lines / len(lines)
        new_size = math.floor(default_size * scale_factor)
        out = f"<size={new_size}>" + " \\n".join(lines) + "</size>"
    else:
        out = " \\n".join(lines)
    
    return out

def get_text_width(text, ttfont):
    t = ttfont.getBestCmap()
    s = ttfont.getGlyphSet()

    return sum(s[t[ord(char)]].width for char in text)

class Preprocessor:
    def __init__(self):
        self.font = prepare_font()
    
    def fix(self, text, interm_path):
        path = interm_path[len(util.MDB_FOLDER_EDITING):].replace("\\", "/")

        if path not in MAX_WIDTHS:
            return text
        
        width_data = MAX_WIDTHS[path]
        return fix_newlines(text, width_data, self.font)

# def main():
#     font_path = prepare_font()
#     fix_newlines(font_path)

# if __name__ == "__main__":
#     main()
