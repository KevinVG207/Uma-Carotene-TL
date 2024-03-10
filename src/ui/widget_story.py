from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
import util
import os
import json
import ui.common as common
from bs4 import BeautifulSoup as bs

TOP_LEVEL = {
    "00": None,
    "01": "01 Tutorial",
    "02": "02 Main Story",
    "04": "04 Chara Story",
    "08": "08 Scenario Intro",
    "09": "09 Story Events",
    "10": "10 Anniversary",
    "11": None,
    "12": None,
    "13": None,
    "40": "40 Scenario Training Event",
    "50": "50 Uma Training Event",
    "80": "80 R Support Event",
    "82": "82 SR Support Event",
    "83": "83 SSR Support Event",
}

class Ui_story_editor(QWidget):
    root_dir = util.ASSETS_FOLDER_EDITING + "story"

    def __init__(self, base_widget=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.base_widget = base_widget

        self.changed = False

        self.marked_item = None

        self.block_changed = False

        self.loaded_chapter = None
        self.loaded_path = None
        self.box_items = []

        self.chara_name_dict = {}
        json_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "6.json")
        chara_name_data = util.load_json(json_path)
        for entry in chara_name_data:
            if not entry.get("text"):
                continue
            char_id = json.loads(entry["keys"])[0][1]
            self.chara_name_dict[str(char_id)] = entry["text"]

        self.setupUi(self)
        self.set_fonts()
        self.setFixedSize(self.size())

        self.bold_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.bold_shortcut.activated.connect(lambda: self.apply_formatting(self.format_bold))
        self.italic_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        self.italic_shortcut.activated.connect(lambda: self.apply_formatting(self.format_italic))
    
    def set_changed(self):
        self.changed = True
        self.base_widget.set_changed(self)
    
    def set_unchanged(self):
        self.changed = False
        self.base_widget.set_unchanged(self)

    def fill_branch(self, parent, path):
        # Add files/paths to the tree
        # First, delete any existing children
        if isinstance(parent, QTreeWidgetItem):
            if parent.data(0, Qt.UserRole + 2):
                return
            parent.takeChildren()
            parent.setData(0, Qt.UserRole + 2, True)  # Loaded

        for file_path in os.listdir(path):
            full_path = os.path.join(path, file_path)

            is_dir = os.path.isdir(full_path)
            ends_json = file_path.endswith(".json")

            if not is_dir and not ends_json:
                continue

            editing_path = full_path[len(self.root_dir) + 1:]
            segments = editing_path.split("\\")

            item_text = os.path.basename(full_path)

            # Top Level
            if len(segments) == 1 and TOP_LEVEL.get(segments[0]):
                item_text = TOP_LEVEL.get(segments[0])
            
            # Character stories
            elif len(segments) == 2 and segments[0] in ["04", "50", "80"]:
                # Load character names
                en_name = self.chara_name_dict.get(segments[1])
                if en_name:
                    item_text = f"{segments[1]} {en_name}"

            item = QTreeWidgetItem(parent)
            item.setText(0, item_text)
            item.setData(0, Qt.UserRole, False)  # Not a directory
            item.setData(0, Qt.UserRole + 1, full_path)  # Store the file path
            item.setData(0, Qt.UserRole + 2, False)  # Not loaded

            if is_dir:
                item.setData(0, Qt.UserRole, True)  # Directory
                # If it's a directory, add a dummy item to it
                dummy = QTreeWidgetItem(item)
                dummy.setText(0, "Loading...")
                # item.setData(0, Qt.UserRole + 2, dummy)

    def on_tree_item_expanded(self, item):
        if item.data(0, Qt.UserRole):
            self.fill_branch(item, item.data(0, Qt.UserRole + 1))
            return
        
        # # If it's a file, load it
        # file_path = item.data(0, Qt.UserRole + 1)
        # self.load_chapter(file_path)

    def on_tree_item_clicked(self, item, column):
        if item.data(0, Qt.UserRole):
            return
        
        # If it's a file, load it
        file_path = item.data(0, Qt.UserRole + 1)
        self.load_chapter(file_path, item)

    def set_item_marked(self, item: QTreeWidgetItem):
        if self.marked_item:
            self.set_item_unmarked(self.marked_item)
        self.marked_item = item

        # item.setBackground(0, QtGui.QColor(230, 230, 230))
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)

    def set_item_unmarked(self, item: QTreeWidgetItem):
        # item.setBackground(0, QtGui.QColor(255, 255, 255))
        font = item.font(0)
        font.setBold(False)
        item.setFont(0, font)

    def next_chapter(self):
        if not self.marked_item:
            return

        next_item = self.treeWidget.itemBelow(self.marked_item)
        if next_item:
            self.on_tree_item_clicked(next_item, 0)
    
    def prev_chapter(self):
        if not self.marked_item:
            return

        prev_item = self.treeWidget.itemAbove(self.marked_item)
        if prev_item:
            self.on_tree_item_clicked(prev_item, 0)
    
    def load_chapter(self, file_path, item):
        self.set_item_marked(item)
        self.loaded_chapter = util.load_json(file_path)
        self.loaded_path = file_path

        # Prepare the combobox
        self.box_items = []
        self.cmb_textblock.clear()
        for i, block in enumerate(self.loaded_chapter["data"]):
            if not block.get("source_name") and not block.get("source"):
                continue
            self.box_items.append(i)
            preview = block.get('source').replace("\n", "")[:10]
            self.cmb_textblock.addItem(f"{i:03} - {preview}")
        
        self.cmb_textblock.setCurrentIndex(0)
    
    def next_block(self):
        if not self.box_items:
            return

        self.store_block()

        current_index = self.cmb_textblock.currentIndex()
        if current_index < len(self.box_items) - 1:
            self.cmb_textblock.setCurrentIndex(current_index + 1)
    
    def prev_block(self):
        if not self.box_items:
            return
        
        self.store_block()

        current_index = self.cmb_textblock.currentIndex()
        if current_index > 0:
            self.cmb_textblock.setCurrentIndex(current_index - 1)
    
    def load_block(self):
        if not self.box_items:
            return
        
        self.store_block()

        block_index = self.box_items[self.cmb_textblock.currentIndex()]

        block = self.loaded_chapter["data"][block_index]
        source_name = block.get("source_name")
        en_name = block.get("name")
        source_text = block.get("source")
        en_text = block.get("text")

        self.set_text(source_name, self.txt_source_name)
        self.set_text(en_name, self.txt_en_name)
        self.set_text(source_text, self.txt_source_text)
        self.set_text(en_text, self.txt_en_text)
    
    def store_block(self):
        if not self.box_items:
            return
        
        if not self.block_changed:
            return
        self.block_changed = False

        block_index = self.box_items[self.cmb_textblock.currentIndex()]

        block = self.loaded_chapter["data"][block_index]
        block["name"] = self.get_text(self.txt_en_name)
        block["text"] = self.get_text(self.txt_en_text)
    
    def on_block_changed(self, widget: QTextEdit):
        self.block_changed = True
    
    def save_chapter(self):
        if not self.loaded_chapter:
            return

        self.store_block()

        # TODO: After testing, should overwrite
        new_path = self.loaded_path + ".new"

        util.save_json(new_path, self.loaded_chapter)


    def set_text(self, text: str, widget: QTextEdit):
        text = text.replace("\n", "<br>")

        # text = text.replace("<", "&lt;")
        # text = text.replace(">", "&gt;")

        # Only add specific tags
        text = text.replace("&lt;b&gt;", "<b>")
        text = text.replace("&lt;/b&gt;", "</b>")
        text = text.replace("&lt;i&gt;", "<i>")
        text = text.replace("&lt;/i&gt;", "</i>")
        text = text.replace("&lt;br&gt;", "<br>")

        text = text.replace("<b>", "<span style=\"font-weight: 600; color: #A00;\">")
        text = text.replace("</b>", "</span>")

        cur_cursor = widget.textCursor()
        cur_pos = cur_cursor.position()
        has_sel = False

        if cur_cursor.hasSelection():
            has_sel = True
            sel_start = cur_cursor.selectionStart()
            sel_end = cur_cursor.selectionEnd()

        widget.setHtml(text)

        new_cursor = widget.textCursor()

        if has_sel:
            new_cursor.setPosition(sel_start)
            new_cursor.setPosition(sel_end, QTextCursor.KeepAnchor)

        else:
            new_cursor.setPosition(cur_pos)
        
        widget.setTextCursor(new_cursor)
    

    def get_text(self, widget: QTextEdit) -> str:
        text = widget.toHtml()
        print(text)

        soup = bs(text, "html.parser")
        p_tag = soup.find("p")

        # Replace any spans with class fake-bold with <b> tags
        for span in p_tag.find_all("span"):
            if 'font-style:italic' in span.get("style", ""):
                span.name = "i"
                del span["style"]
                del span["class"]

            if 'font-weight:600' in span.get("style", ""):
                span.name = "b"
                del span["style"]
                del span["class"]
        
        # Get the inner text and elements
        text = p_tag.decode_contents()

        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")

        text = text.replace("<br>", "\n")

        return text

    
    def set_fonts(self):
        fnt = common.uma_font(16)
        self.txt_source_name.setFont(fnt)
        self.txt_en_name.setFont(fnt)
        self.txt_source_text.setFont(fnt)
        self.txt_en_text.setFont(fnt)
    

    def format_bold(self, text, sel_start, sel_end):
        return self.format_text(text, sel_start, sel_end, bold=True)
    
    def format_italic(self, text, sel_start, sel_end):
        return self.format_text(text, sel_start, sel_end, italic=True)

    def format_text(self, text: str, sel_start, sel_end, bold=False, italic=False) -> str:
        in_tag = False
        tag_active = False
        fill_value = None

        if not bold and not italic:
            raise ValueError("No formatting specified")

        text_chars = []

        cur_tags = []
        cur_tag = ""

        i = 0
        for char in text:
            is_bold = False
            is_italic = False

            if char == "<":
                in_tag = True
                tag_active = True
                cur_tag = ""
                continue

            if in_tag and char == "/":
                tag_active = False
                continue

            if in_tag and char == ">":
                in_tag = False

                if not tag_active:
                    cur_tags.pop()
                else:
                    cur_tags.append(cur_tag)
                continue

            if in_tag:
                cur_tag += char
                continue

            if "b" in cur_tags:
                is_bold = True

            if "i" in cur_tags:
                is_italic = True

            if sel_start <= i < sel_end:
                if bold:
                    if fill_value is None:
                        fill_value = not is_bold
                    is_bold = fill_value
                if italic:
                    if fill_value is None:
                        fill_value = not is_italic
                    is_italic = fill_value

            text_chars.append((char, is_bold, is_italic))
            i += 1

        # Reconstruct the text
        new_text = ""
        prev_bold = False
        prev_italic = False

        tag_stack = []

        for char, is_bold, is_italic in text_chars:
            if prev_bold and prev_italic:
                if prev_bold != is_bold or prev_italic != is_italic:
                    for i in range(len(tag_stack)):
                        new_text += tag_stack.pop()
                    prev_bold = False
                    prev_italic = False
            
            if prev_bold != is_bold:
                if is_bold:
                    new_text += "<b>"
                    tag_stack.append("</b>")
                else:
                    new_text += tag_stack.pop()
            if prev_italic != is_italic:
                if is_italic:
                    new_text += "<i>"
                    tag_stack.append("</i>")
                else:
                    new_text += tag_stack.pop()
            
            new_text += char

            prev_bold = is_bold
            prev_italic = is_italic
        
        if prev_bold:
            new_text += "</b>"
        if prev_italic:
            new_text += "</i>"
        
        return new_text


    
    def apply_formatting(self, format_func):
        if not self.txt_en_text.hasFocus():
            return
        
        cursor = self.txt_en_text.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            formatted = format_func(self.get_text(self.txt_en_text), start, end)
            print(formatted)
            self.set_text(formatted, self.txt_en_text)


    def setupUi(self, story_editor):
        if not story_editor.objectName():
            story_editor.setObjectName(u"story_editor")
        story_editor.resize(1280, 540)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(story_editor.sizePolicy().hasHeightForWidth())
        story_editor.setSizePolicy(sizePolicy)
        story_editor.setMinimumSize(QSize(1280, 540))
        story_editor.setWindowTitle(u"Story Editor")
        self.btn_prev_chapter = QPushButton(story_editor)
        self.btn_prev_chapter.setObjectName(u"btn_prev_chapter")
        self.btn_prev_chapter.setGeometry(QRect(10, 10, 75, 23))
        self.btn_prev_chapter.setText(u"<- Prev")
        self.btn_prev_chapter.clicked.connect(self.prev_chapter)
        self.btn_next_chapter = QPushButton(story_editor)
        self.btn_next_chapter.setObjectName(u"btn_next_chapter")
        self.btn_next_chapter.setGeometry(QRect(180, 10, 75, 23))
        self.btn_next_chapter.setText(u"Next ->")
        self.btn_next_chapter.clicked.connect(self.next_chapter)

        self.treeWidget = QTreeWidget(story_editor)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"Story Chapter")
        self.treeWidget.setHeaderItem(__qtreewidgetitem)
        # self.treeWidget.itemClicked.connect(self.on_tree_item_clicked)
        self.treeWidget.itemExpanded.connect(self.on_tree_item_expanded)
        self.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

        self.fill_branch(self.treeWidget, self.root_dir)


        # __qtreewidgetitem1 = QTreeWidgetItem(self.treeWidget)
        # __qtreewidgetitem1.setText(0, u"01 - BLAH");
        # __qtreewidgetitem2 = QTreeWidgetItem(__qtreewidgetitem1)
        # __qtreewidgetitem2.setText(0, u"New Item");
        # __qtreewidgetitem3 = QTreeWidgetItem(__qtreewidgetitem1)
        # __qtreewidgetitem3.setText(0, u"New Item");
        # __qtreewidgetitem4 = QTreeWidgetItem(self.treeWidget)
        # __qtreewidgetitem4.setText(0, u"02 - BLAH");
        # __qtreewidgetitem5 = QTreeWidgetItem(__qtreewidgetitem4)
        # __qtreewidgetitem5.setText(0, u"New Item");
        # __qtreewidgetitem6 = QTreeWidgetItem(__qtreewidgetitem4)
        # __qtreewidgetitem6.setText(0, u"New Item");
        self.treeWidget.setObjectName(u"treeWidget")
        self.treeWidget.setGeometry(QRect(10, 40, 251, 491))
        self.groupBox = QGroupBox(story_editor)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(1059, 0, 211, 531))
        self.groupBox.setTitle(u"Actions")
        self.pushButton_5 = QPushButton(self.groupBox)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setGeometry(QRect(10, 20, 191, 23))
        self.pushButton_5.setText(u"Auto-translate speakers")
        self.pushButton_6 = QPushButton(self.groupBox)
        self.pushButton_6.setObjectName(u"pushButton_6")
        self.pushButton_6.setGeometry(QRect(10, 50, 191, 23))
        self.pushButton_6.setText(u"Goto next untranslated speaker")
        self.pushButton_9 = QPushButton(self.groupBox)
        self.pushButton_9.setObjectName(u"pushButton_9")
        self.pushButton_9.setGeometry(QRect(10, 90, 191, 23))
        self.pushButton_9.setText(u"Goto next untranslated choices")
        self.pushButton_10 = QPushButton(self.groupBox)
        self.pushButton_10.setObjectName(u"pushButton_10")
        self.pushButton_10.setGeometry(QRect(10, 130, 191, 23))
        self.pushButton_10.setText(u"Goto next untranslated dialogue")
        self.textEdit_3 = QTextEdit(self.groupBox)
        self.textEdit_3.setObjectName(u"textEdit_3")
        self.textEdit_3.setGeometry(QRect(10, 480, 191, 41))
        self.textEdit_3.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">EN goes here</p></body></html>")
        self.textEdit_4 = QTextEdit(self.groupBox)
        self.textEdit_4.setObjectName(u"textEdit_4")
        self.textEdit_4.setEnabled(True)
        self.textEdit_4.setGeometry(QRect(10, 430, 191, 41))
        self.textEdit_4.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">JP goes here</p></body></html>")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 410, 71, 16))
        self.label_3.setText(u"Chapter title")
        
        self.txt_source_name = QTextEdit(story_editor)
        self.txt_source_name.setObjectName(u"txt_source_name")
        self.txt_source_name.setGeometry(QRect(270, 40, 401, 41))
        self.txt_source_name.setReadOnly(True)
        
        self.txt_source_text = QTextEdit(story_editor)
        self.txt_source_text.setObjectName(u"textEdit_5")
        self.txt_source_text.setGeometry(QRect(270, 90, 781, 121))
        self.txt_source_text.setReadOnly(True)
        
        self.txt_en_text = QTextEdit(story_editor)
        self.txt_en_text.setObjectName(u"textEdit_6")
        self.txt_en_text.setGeometry(QRect(270, 280, 781, 121))
        self.txt_en_text.textChanged.connect(lambda: self.on_block_changed(self.txt_en_text))
        
        self.txt_en_name = QTextEdit(story_editor)
        self.txt_en_name.setObjectName(u"txt_en_name")
        self.txt_en_name.setGeometry(QRect(270, 230, 401, 41))
        self.txt_en_name.textChanged.connect(lambda: self.on_block_changed(self.txt_en_name))
        
        self.cmb_textblock = QComboBox(story_editor)
        self.cmb_textblock.setObjectName(u"cmb_textblock")
        self.cmb_textblock.setGeometry(QRect(270, 410, 271, 22))
        self.cmb_textblock.currentIndexChanged.connect(self.load_block)

        self.btn_prev_block = QPushButton(story_editor)
        self.btn_prev_block.setObjectName(u"btn_prev_block")
        self.btn_prev_block.setGeometry(QRect(550, 410, 75, 23))
        self.btn_prev_block.setText(u"<- Prev")
        self.btn_prev_block.clicked.connect(self.prev_block)

        self.btn_next_block = QPushButton(story_editor)
        self.btn_next_block.setObjectName(u"pushButton_4")
        self.btn_next_block.setGeometry(QRect(630, 410, 75, 23))
        self.btn_next_block.setText(u"Next ->")
        self.btn_next_block.clicked.connect(self.next_block)
        
        self.label = QLabel(story_editor)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(90, 10, 81, 21))
        self.label.setText(u"Chapter")
        self.label.setAlignment(Qt.AlignCenter)
        self.label_2 = QLabel(story_editor)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(270, 10, 81, 21))
        self.label_2.setText(u"Textblock")
        self.checkBox = QCheckBox(story_editor)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setGeometry(QRect(960, 490, 81, 20))
        self.checkBox.setText(u"Autosave")
        self.checkBox.setChecked(True)
        self.pushButton_7 = QPushButton(story_editor)
        self.pushButton_7.setObjectName(u"pushButton_7")
        self.pushButton_7.setGeometry(QRect(970, 220, 75, 23))
        self.pushButton_7.setText(u"Listen")

        self.btn_save = QPushButton(story_editor)
        self.btn_save.setObjectName(u"pushButton_8")
        self.btn_save.setGeometry(QRect(954, 510, 91, 23))
        self.btn_save.setText(u"Save chapter")
        self.btn_save.clicked.connect(self.save_chapter)

        self.pushButton_11 = QPushButton(story_editor)
        self.pushButton_11.setObjectName(u"pushButton_11")
        self.pushButton_11.setEnabled(False)
        self.pushButton_11.setGeometry(QRect(874, 220, 91, 23))
        self.pushButton_11.setText(u"Show choices")
        self.pushButton_12 = QPushButton(story_editor)
        self.pushButton_12.setObjectName(u"pushButton_12")
        self.pushButton_12.setGeometry(QRect(270, 510, 101, 23))
        self.pushButton_12.setText(u"Discard changes")

