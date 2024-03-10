from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
import util
import os
import json
import ui.common as common
import intermediate
import _patch
import postprocess
import shutil
from settings import settings
import ui.widget_story_utils as sutils
import ui.widget_story_choices as story_choices
import copy

TOP_LEVEL = {
    "00": None,
    "01": "01 Tutorial",
    "02": "02 Main Story",
    "04": "04 Character Stories",
    "08": "08 Scenario Intro",
    "09": "09 Story Events",
    "10": "10 Anniversary",
    "11": None,
    "12": None,
    "13": None,
    "40": "40 Scenario Training Events",
    "50": "50 Uma Training Events",
    "80": "80 R Support Events",
    "82": "82 SR Support Events",
    "83": "83 SSR Support Events",
}

class Ui_story_editor(QWidget):
    root_dir = util.ASSETS_FOLDER_EDITING + "story"
    font_size = 16

    def __init__(self, base_widget=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.base_widget = base_widget

        self.changed = False
        self.ignore_updates = False

        self.cur_open_block = None

        self.marked_item = None

        self.block_changed = False

        self.save_timeout = QTimer()
        self.save_timeout.setSingleShot(True)
        self.save_timeout.timeout.connect(self.handle_save_timeout)

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
        self.bold_shortcut.activated.connect(lambda: self.selection_toggle_format(self.txt_en_text, bold=True))
        self.italic_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        self.italic_shortcut.activated.connect(lambda: self.selection_toggle_format(self.txt_en_text, bold=False))
    
    def set_changed(self):
        self.changed = True
        self.base_widget.set_changed(self)
        if not self.marked_item.text(0).endswith("*"):
            self.marked_item.setText(0, self.marked_item.text(0) + "*")
    
    def set_unchanged(self):
        self.changed = False
        self.base_widget.set_unchanged(self)
        if self.marked_item.text(0).endswith("*"):
            self.marked_item.setText(0, self.marked_item.text(0)[:-1])
        self.set_choices_unchanged()
    
    def set_choices_unchanged(self):
        if self.btn_choices.text().endswith("*"):
            self.btn_choices.setText(self.btn_choices.text()[:-1])
    
    def set_choices_changed(self):
        if not self.btn_choices.text().endswith("*"):
            self.btn_choices.setText(self.btn_choices.text() + "*")

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

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column):
        if item.data(0, Qt.UserRole):
            item.setExpanded(not item.isExpanded())
            return
        
        # If it's a file, load it
        file_path = item.data(0, Qt.UserRole + 1)
        self.load_chapter(file_path, item)

    def set_item_marked(self, item: QTreeWidgetItem):
        if self.marked_item:
            self.set_item_unmarked(self.marked_item)
        self.marked_item = item

        while True:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            
            if not item.parent():
                break
            item = item.parent()

        # item.setBackground(0, QtGui.QColor(230, 230, 230))
        # font = item.font(0)
        # font.setBold(True)
        # item.setFont(0, font)

    def set_item_unmarked(self, item: QTreeWidgetItem):
        # item.setBackground(0, QtGui.QColor(255, 255, 255))
        while True:
            font = item.font(0)
            font.setBold(False)
            item.setFont(0, font)

            if not item.parent():
                break
            item = item.parent()

    def next_chapter(self):
        if not self.marked_item:
            return

        next_item = self.treeWidget.itemBelow(self.marked_item)
        if next_item:
            if next_item.parent() != self.marked_item.parent():
                return

            self.on_tree_item_clicked(next_item, 0)
    
    def prev_chapter(self):
        if not self.marked_item:
            return

        prev_item = self.treeWidget.itemAbove(self.marked_item)
        if prev_item:
            if prev_item.parent() != self.marked_item.parent():
                return
            self.on_tree_item_clicked(prev_item, 0)

    def ask_close(self):
        return self.ask_save()

    def ask_save(self):
        if self.changed:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Question)
            msgbox.setText("You have unsaved story changes. Do you want to save first?")
            msgbox.setWindowTitle("Story Changes")
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msgbox.setDefaultButton(QMessageBox.Cancel)
            ret = msgbox.exec()

            if ret == QMessageBox.Cancel:
                return False
            
            if ret == QMessageBox.Yes:
                self.save_chapter()
            
            if ret == QMessageBox.No:
                self.set_unchanged()
        
        return True
    
    def load_chapter(self, file_path, item):
        if self.changed:
            if not self.ask_save():
                return

        self.cur_open_block = None
        self.block_changed = False
        self.box_items = []
        self.cmb_textblock.clear()

        self.set_item_marked(item)
        self.loaded_chapter = util.load_json(file_path)
        self.loaded_path = file_path

        # Prepare the combobox
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

        # self.store_block()

        current_index = self.cmb_textblock.currentIndex()
        if current_index < len(self.box_items) - 1:
            self.cmb_textblock.setCurrentIndex(current_index + 1)
    
    def prev_block(self):
        if not self.box_items:
            return
        
        # self.store_block()

        current_index = self.cmb_textblock.currentIndex()
        if current_index > 0:
            self.cmb_textblock.setCurrentIndex(current_index - 1)
    
    def load_block(self):
        if not self.box_items:
            return
        
        if self.chkb_autosave.isChecked():
            self.save_chapter()
        else:
            self.store_block()

        block_index = self.box_items[self.cmb_textblock.currentIndex()]
        self.cur_open_block = block_index

        block = self.loaded_chapter["data"][block_index]
        source_name = block.get("source_name")
        en_name = block.get("name")
        source_text = block.get("source")
        en_text = block.get("text")

        self.ignore_updates = True
        sutils.set_text(source_name, self.txt_source_name)
        sutils.set_text(en_name, self.txt_en_name)
        sutils.set_text(source_text, self.txt_source_text)
        sutils.set_text(en_text, self.txt_en_text)
        self.ignore_updates = False

        self.btn_choices.setEnabled(False)
        # self.btn_choices.font().setBold(False)
        btn_font = self.btn_choices.font()
        btn_font.setBold(False)
        self.btn_choices.setStyleSheet("")
        if block.get("choices"):
            self.btn_choices.setEnabled(True)
            btn_font.setBold(True)
            self.btn_choices.setStyleSheet("color: rgb(0, 100, 0);")
        self.btn_choices.setFont(btn_font)
    
    def store_block(self):
        if not self.box_items:
            return
        
        if not self.cur_open_block:
            return
        
        if not self.block_changed:
            return
        self.block_changed = False

        # print("Storing block")

        block_index = self.cur_open_block

        block = self.loaded_chapter["data"][block_index]
        block["name"] = sutils.get_text(self.txt_en_name)
        block["text"] = sutils.get_text(self.txt_en_text)
    
    def on_block_changed(self, widget: QPlainTextEdit):
        if self.ignore_updates:
            return

        self.block_changed = True
        self.set_changed()
        self.save_timeout.start(500)
        # print("Set save timeout")
    
    def save_chapter(self):
        if not self.loaded_chapter:
            return

        self.store_block()

        # print("Saving chapter")

        util.save_json(self.loaded_path, self.loaded_chapter)
        self.set_unchanged()
    
    def handle_save_timeout(self):
        # print("Save timeout")
        if self.chkb_autosave.isChecked():
            self.save_chapter()

    
    def set_fonts(self):
        fnt = common.uma_font(self.font_size)
        self.txt_source_name.setFont(fnt)
        self.txt_en_name.setFont(fnt)
        self.txt_source_text.setFont(fnt)
        self.txt_en_text.setFont(fnt)
    
    def selection_toggle_format(self, widget: QPlainTextEdit, bold=True):
        # if not widget.hasFocus():
        #     return
        if not widget.textCursor().hasSelection():
            return
        
        cursor = widget.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        cursor.setPosition(start + 1)
        if bold:
            value = not cursor.charFormat().fontWeight() == 75
        else:
            value = not cursor.charFormat().fontItalic()

        text = widget.toPlainText()

        prev_formats = []
        for i in range(start, end):
            cursor.setPosition(i+1)
            char_format = cursor.charFormat()
            prev_formats.append(char_format)

        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.deleteChar()

        for i in range(start, end):
            cursor.setPosition(i)
            char_format = prev_formats[i - start]
            if bold:
                char_format.setFontWeight(QFont.Normal)
                char_format.setTextOutline(QPen(0))
                if value:
                    sutils._make_bold(char_format)
            else:
                char_format.setFontItalic(False)
                if value:
                    char_format.setFontItalic(True)
            cursor.setCharFormat(char_format)
            cursor.insertText(text[i])
        
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        widget.setTextCursor(cursor)


    def autosave_toggled(self):
        if self.chkb_autosave.isChecked():
            self.save_chapter()
        settings.autosave_story_editor = self.chkb_autosave.isChecked()

    
    def patch_chapter(self):
        if not self.loaded_chapter:
            return
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.btn_apply_chapter.setEnabled(False)
        
        self.save_chapter()

        # Patch the chapter
        editing_path = self.loaded_path
        tl_path = util.ASSETS_FOLDER + editing_path[len(util.ASSETS_FOLDER_EDITING):]
        intermediate.process_asset(editing_path)
        postprocess._fix_story((util.load_json(tl_path), tl_path))
        _patch._import_story(util.load_json(tl_path))

        self.btn_apply_chapter.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def unpatch_chapter(self):
        if not self.loaded_chapter:
            return
        
        self.btn_unpatch.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        asset_path = util.get_asset_path(self.loaded_chapter['hash'])
        backup_path = asset_path + ".bak"

        if os.path.exists(backup_path):
            shutil.move(backup_path, asset_path)

        self.btn_unpatch.setEnabled(True)
        QApplication.restoreOverrideCursor()


    def choices_clicked(self):
        if not self.loaded_chapter:
            return
        
        if not self.cur_open_block:
            return
        
        block = self.loaded_chapter["data"][self.cur_open_block]
        if not block.get("choices"):
            return
        
        choices = block["choices"]
        prev_choices = copy.deepcopy(choices)
        dialog = story_choices.story_choice_dialog(choices)
        dialog.exec_()

        changed = False
        for i, choice in enumerate(choices):
            if choice['text'] != prev_choices[i]['text']:
                changed = True
                break
        
        if changed:
            self.set_changed()
            self.save_timeout.start(500)
            self.set_choices_changed()





    def setupUi(self, story_editor):
        if not story_editor.objectName():
            story_editor.setObjectName(u"story_editor")
        story_editor.resize(1280, 468)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(story_editor.sizePolicy().hasHeightForWidth())
        story_editor.setSizePolicy(sizePolicy)
        story_editor.setMinimumSize(QSize(1280, 468))
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
        self.treeWidget.setGeometry(QRect(10, 40, 251, 411))
        self.groupBox = QGroupBox(story_editor)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(1059, 0, 211, 461))
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
        self.textEdit_3 = QPlainTextEdit(self.groupBox)
        self.textEdit_3.setObjectName(u"textEdit_3")
        self.textEdit_3.setGeometry(QRect(10, 410, 191, 41))
        self.textEdit_4 = QPlainTextEdit(self.groupBox)
        self.textEdit_4.setObjectName(u"textEdit_4")
        self.textEdit_4.setEnabled(True)
        self.textEdit_4.setGeometry(QRect(10, 360, 191, 41))
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 340, 71, 16))
        self.label_3.setText(u"Chapter title")
        
        self.txt_source_name = QPlainTextEdit(story_editor)
        self.txt_source_name.setObjectName(u"txt_source_name")
        self.txt_source_name.setGeometry(QRect(270, 40, 401, 41))
        self.txt_source_name.setReadOnly(True)
        self.txt_source_name.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        self.txt_source_text = QPlainTextEdit(story_editor)
        self.txt_source_text.setObjectName(u"textEdit_5")
        self.txt_source_text.setGeometry(QRect(270, 90, 781, 121))
        self.txt_source_text.setReadOnly(True)
        self.txt_source_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        self.txt_en_text = QPlainTextEdit(story_editor)
        self.txt_en_text.setObjectName(u"textEdit_6")
        self.txt_en_text.setGeometry(QRect(270, 280, 781, 121))
        self.txt_en_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.txt_en_text.textChanged.connect(lambda: self.on_block_changed(self.txt_en_text))
        
        self.txt_en_name = QPlainTextEdit(story_editor)
        self.txt_en_name.setObjectName(u"txt_en_name")
        self.txt_en_name.setGeometry(QRect(270, 230, 401, 41))
        self.txt_en_name.setLineWrapMode(QPlainTextEdit.NoWrap)
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
        self.chkb_autosave = QCheckBox(story_editor)
        self.chkb_autosave.setObjectName(u"chkb_autosave")
        self.chkb_autosave.setGeometry(QRect(960, 420, 81, 20))
        self.chkb_autosave.setText(u"Autosave")
        self.chkb_autosave.setChecked(settings.autosave_story_editor)
        self.chkb_autosave.stateChanged.connect(self.autosave_toggled)

        # self.pushButton_7 = QPushButton(story_editor)
        # self.pushButton_7.setObjectName(u"pushButton_7")
        # self.pushButton_7.setGeometry(QRect(970, 220, 75, 23))
        # self.pushButton_7.setText(u"Listen")

        self.btn_save = QPushButton(story_editor)
        self.btn_save.setObjectName(u"pushButton_8")
        self.btn_save.setGeometry(QRect(954, 440, 91, 23))
        self.btn_save.setText(u"Save chapter")
        self.btn_save.clicked.connect(self.save_chapter)

        self.btn_choices = QPushButton(story_editor)
        self.btn_choices.setObjectName(u"pushButton_11")
        self.btn_choices.setEnabled(False)
        self.btn_choices.setGeometry(QRect(960, 220, 91, 23))
        self.btn_choices.setText(u"Show choices")
        self.btn_choices.setEnabled(False)
        self.btn_choices.clicked.connect(self.choices_clicked)

        self.btn_apply_chapter = QPushButton(story_editor)
        self.btn_apply_chapter.setObjectName(u"btn_apply_chapter")
        self.btn_apply_chapter.setGeometry(QRect(810, 440, 131, 23))
        self.btn_apply_chapter.setText(u"Save && apply to game")
        self.btn_apply_chapter.clicked.connect(self.patch_chapter)

        self.btn_bold = QPushButton(story_editor)
        self.btn_bold.setObjectName(u"btn_bold")
        self.btn_bold.setGeometry(QRect(680, 250, 75, 23))
        self.btn_bold.setText(u"Bold")
        self.btn_bold.setStyleSheet("font-weight: bold;")
        self.btn_bold.clicked.connect(lambda: self.selection_toggle_format(self.txt_en_text, bold=True))

        self.btn_italic = QPushButton(story_editor)
        self.btn_italic.setObjectName(u"btn_italic")
        self.btn_italic.setGeometry(QRect(760, 250, 75, 23))
        self.btn_italic.setText(u"Italic")
        # self.btn_italic.setStyleSheet("font-style: italic;")
        self.btn_italic.clicked.connect(lambda: self.selection_toggle_format(self.txt_en_text, bold=False))

        self.btn_unpatch = QPushButton(story_editor)
        self.btn_unpatch.setObjectName(u"btn_unpatch")
        self.btn_unpatch.setGeometry(QRect(700, 440, 101, 23))
        self.btn_unpatch.setText(u"Unpatch chapter")
        self.btn_unpatch.clicked.connect(self.unpatch_chapter)

        self.lbl_length_marker = QLabel(story_editor)
        self.lbl_length_marker.setObjectName(u"lbl_length_marker")
        self.lbl_length_marker.setGeometry(QRect(1005, 281, 1, 119))
        self.lbl_length_marker.setAutoFillBackground(False)
        self.lbl_length_marker.setStyleSheet(u"background-color: rgb(255, 0, 0);")

