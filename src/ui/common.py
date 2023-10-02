from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import math
import util
import os
import json

MDB_CAT_NAMES = {
    "text_data": {
        "1": "UI",
        "2": "Errors",
        "3": "Tutorial",
        "4": "(Auto) Outfit+Chara Combo",
        "5": "Outfit Titles",
        "6": "Character Names",
        "7": "Voice Actors",
        "8": "Residence",
        "9": "Weight",
        "10": "? Item Descriptions",
        "13": "? Gacha Types",
        "14": "Clothes",
        "15": "Clothes 2",
        "16": "Song Names",
        "17": "Song Credits",
        "23": "Item Names",
        "24": "Item Descriptions",
        "25": "How to obtain X",
        "26": "Gacha Banners",
        "27": "?",
        "28": "Race Names (Long)",
        "29": "Race Names (Short)",
        "170": "Character Names",
        "182": "Chara Names (katakana)"
    }
}
MDB_CAT_NAMES_LOADED = False

def get_mdb_cat_names():
    global MDB_CAT_NAMES_LOADED
    global MDB_CAT_NAMES

    if not MDB_CAT_NAMES_LOADED:
        MDB_CAT_NAMES_LOADED = True
        chara_json = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "170.json")
        if not os.path.exists(chara_json):
            raise FileNotFoundError(f"Json not found: {chara_json}")
        
        MDB_CAT_NAMES["character_system_text"] = {}

        chara_data = util.load_json(chara_json)
        for chara in chara_data:
            chara_id = str(json.loads(chara['keys'])[0][-1])
            chara_name = chara.get("text", "")
            MDB_CAT_NAMES["character_system_text"][chara_id] = chara_name

    return MDB_CAT_NAMES

class ExpandingTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document().contentsChanged.connect(self.size_change)

        self.height_min = 23
        self.height_max = 65000
    
    def size_change(self):
        doc_height = math.ceil(self.document().size().height()) + 2
        doc_height += 17  # TODO: Scrollbar

        if self.height_min <= doc_height <= self.height_max:
            self.setMinimumHeight(doc_height)
            self.setMaximumHeight(doc_height)
    
    def line_spacing(self, spacing):
        text_cursor = self.textCursor()

        text_block_format = QTextBlockFormat()
        text_cursor.clearSelection()
        text_cursor.select(QTextCursor.Document)
        text_block_format.setLineHeight(spacing, QTextBlockFormat.LineDistanceHeight)
        text_cursor.mergeBlockFormat(text_block_format)

    def insertFromMimeData(self, source: QMimeData) -> None:
        self.insertPlainText(source.text())


UMA_FONT_FAMILY = None
def uma_font(font_size=8, weight=QFont.Weight.Normal, italic=False):
    global UMA_FONT_FAMILY
    if not UMA_FONT_FAMILY:
        font_path = os.path.join(util.MDB_FOLDER_EDITING, "font", "dynamic01.otf")

        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font not found: {font_path}")
        
        font_id = QFontDatabase.addApplicationFont(font_path)

        if font_id == -1:
            raise RuntimeError(f"Failed to load font: {font_path}")
        
        UMA_FONT_FAMILY = QFontDatabase.applicationFontFamilies(font_id)[0]

    font = QFont(UMA_FONT_FAMILY, font_size, weight, italic)
    font.setStyleStrategy(QFont.PreferAntialias)
    # font.setHintingPreference(QFont.PreferNoHinting)

    return font