import util
import shutil
import os
import math
import re


def fix_newlines(text, font, width_data):
    text = text.replace("\r", "").replace("\n", "").replace("\\r", "").replace("\\n", "").strip()

    # text = re.sub(r"<.*?>", "", text)

    lines = split_text_into_lines(text, font, width_data)
    return lines

def split_text_into_lines(text, font, width_data):
    """Split text into lines based on max width, using font."""
    max_width, max_lines, default_size = width_data

    lines = []
    cur_line = ""
    for word in text.split(" "):
        # Check if word fits on current line
        future_line = cur_line + " " + word if cur_line else word
        if util.get_text_width(future_line, font) > max_width:
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


# Set max width per category
PP_FUNCS = {
    "text_data/DUMMY.json": (fix_newlines, (13000, None, None)),
}

class Preprocessor:
    def __init__(self):
        self.font = util.prepare_font()
    
    def fix(self, text, interm_path):
        path = interm_path[len(util.MDB_FOLDER_EDITING):].replace("\\", "/")

        if path not in PP_FUNCS:
            return text
        
        func, args = PP_FUNCS[path]
        return func(text, self.font, *args)

def main():
    font_path = util.prepare_font()
    b = 'Matikanefukukitar'
    a = util.get_text_width(b, font_path)
    print(a)

if __name__ == "__main__":
    main()
