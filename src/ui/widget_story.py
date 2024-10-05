from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import util
import os
import json
import ui.common as common
import intermediate
import _patch
import postprocess
import hachimi
import shutil
from settings import settings
import ui.widget_story_utils as sutils
import ui.widget_story_choices as story_choices
import ui.widget_story_speakers as story_speakers
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
    "00000": "home/Normal",
    "00001": "home/Birthday",
    "00002": "home/Special?",
}

HOME_SUB = {
    "01": "Solo",
    "02": "Duo",
    "03": "Trio",
}

class Ui_story_editor(QWidget):
    root_dir = util.ASSETS_FOLDER_EDITING + "story"
    font_size = 16
    timeout_ms = 500
    sync_timeout_ms = 200

    def __init__(self, base_widget=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print("Setting up story editor widget")

        self.base_widget = base_widget

        self.changed = False
        self.ignore_updates = False

        self.cur_open_block = None

        self.marked_item = None

        self.block_changed = False

        self.save_timeout = QTimer()
        self.save_timeout.setSingleShot(True)
        self.save_timeout.timeout.connect(self.handle_save_timeout)

        self.sync_timeout = QTimer()
        self.sync_timeout.setSingleShot(True)
        self.sync_timeout.timeout.connect(self.handle_sync_timeout)

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

    def fill_branch(self, parent, path, home=False):
        # Add files/paths to the tree
        # First, delete any existing children
        if isinstance(parent, QTreeWidgetItem):
            if parent.data(0, Qt.UserRole + 2):
                return
            parent.takeChildren()
            parent.setData(0, Qt.UserRole + 2, True)  # Loaded
            if parent.data(0, Qt.UserRole + 3):
                home = True

        for file_path in os.listdir(path):
            full_path = os.path.join(path, file_path)

            is_dir = os.path.isdir(full_path)
            ends_json = file_path.endswith(".json")

            if not is_dir and not ends_json:
                continue

            editing_path = full_path[len(self.root_dir) + 1:]
            segments = editing_path.split("\\")

            item_text = os.path.basename(full_path)

            if home and item_text == "ui":
                continue

            # Top Level
            if len(segments) == 1 and TOP_LEVEL.get(item_text):
                item_text = TOP_LEVEL.get(item_text)
            
            if home and len(segments) == 2 and HOME_SUB.get(segments[-1]):
                item_text += " " + HOME_SUB.get(segments[-1])
            
            # Character stories
            elif (len(segments) == 2 and segments[0] in ["04", "50", "80"]) or (home and len(segments[-1]) == 4):
                # Load character names
                en_name = self.chara_name_dict.get(segments[-1])
                if en_name:
                    item_text = f"{segments[-1]} {en_name}"

            item = QTreeWidgetItem(parent)
            item.setText(0, item_text)
            item.setData(0, Qt.UserRole, False)  # Not a directory
            item.setData(0, Qt.UserRole + 1, full_path)  # Store the file path
            item.setData(0, Qt.UserRole + 2, False)  # Not loaded
            item.setData(0, Qt.UserRole + 3, home)  # Home

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
    
    def expand_all_parents(self, item):
        while item.parent():
            item = item.parent()
            item.setExpanded(True)
    
    def load_chapter(self, file_path, item):
        if self.changed:
            if not self.ask_save():
                return
            
        self.expand_all_parents(item)

        self.cur_open_block = None
        self.block_changed = False
        self.box_items = []
        self.cmb_textblock.clear()
        self.chkb_sync_game.setChecked(False)

        self.set_item_marked(item)
        self.loaded_chapter = util.load_json(file_path)
        self.loaded_path = file_path

        self.ignore_updates = True
        self.txt_chapter_name_source.setPlainText(self.loaded_chapter.get("source_title"))
        self.txt_chapter_name.setPlainText(self.loaded_chapter.get("title"))
        self.ignore_updates = False

        # Prepare the combobox
        for i, block in enumerate(self.loaded_chapter["data"]):
            if not block.get("source_name") and not block.get("source"):
                continue
            self.box_items.append(i)
            preview = block.get('source').replace("\n", "")[:20]
            self.cmb_textblock.addItem(f"{i:03} - {preview}")
        
        
        self.cmb_textblock.setCurrentIndex(0)
        self.update_goto_buttons()
    
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
    
    def reload_block(self):
        block = self.loaded_chapter["data"][self.cur_open_block]
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

    
    def load_block(self):
        if not self.box_items:
            return
        
        if self.chkb_autosave.isChecked():
            self.save_chapter()
        else:
            self.store_block()

        block_index = self.box_items[self.cmb_textblock.currentIndex()]
        self.cur_open_block = block_index

        self.reload_block()

        # if self.chkb_sync_game.isChecked():
        #     self.goto_game()
        self.set_sync_timeout()
    
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
        self.update_goto_buttons()
    
    def on_block_changed(self, widget: sutils.UmaPlainTextEdit):
        if self.ignore_updates:
            return

        self.block_changed = True
        self.set_changed()
        self.set_timeout()
        # print("Set save timeout")
    
    def save_chapter(self):
        if not self.loaded_chapter:
            return

        self.store_block()

        # print("Saving chapter")

        self.loaded_chapter["title"] = sutils.get_text(self.txt_chapter_name)

        util.save_json(self.loaded_path, self.loaded_chapter)
        self.set_unchanged()
    
    def handle_save_timeout(self):
        # print("Save timeout")
        if self.chkb_autosave.isChecked():
            self.save_chapter()
    
    def handle_sync_timeout(self):
        if self.chkb_sync_game.isChecked():
            self.goto_game()

    
    def set_fonts(self):
        fnt = common.uma_font(self.font_size)
        self.txt_source_name.setFont(fnt)
        self.txt_en_name.setFont(fnt)
        self.txt_source_text.setFont(fnt)
        self.txt_en_text.setFont(fnt)
    
    def selection_toggle_format(self, widget: sutils.UmaPlainTextEdit, bold=True):
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
        # _patch._import_story(util.load_json(tl_path))
        tl_data = util.load_json(tl_path)
        hachimi.convert_stories([[tl_data, tl_path]])
        game_path = util.get_game_folder()
        local_out_path = os.path.join(hachimi.HACHIMI_ROOT, "assets", tl_data['file_name'] + ".json")
        out_path = os.path.join(game_path, "hachimi", "localized_data", "assets", tl_data['file_name'] + ".json")
        out_folder = os.path.dirname(out_path)
        os.makedirs(out_folder, exist_ok=True)
        shutil.copy(local_out_path, out_path)
        print(out_path)

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
            self.block_changed = True
            self.set_changed()
            self.set_timeout()
            self.set_choices_changed()

    def set_timeout(self):
        self.save_timeout.start(self.timeout_ms)

    def set_sync_timeout(self):
        self.sync_timeout.start(self.sync_timeout_ms)

    def speaker_clicked(self, *args, **kwargs):
        self.manage_speakers(focus_name=True)

    def manage_speakers(self, focus_name=False, *args, **kwargs):
        if not self.loaded_chapter:
            return
        
        if not self.cur_open_block:
            return


        # Gather all distinct JP speaker names
        speakers = {}

        for i, block in enumerate(self.loaded_chapter["data"]):
            source_name = block.get("source_name")
            name = block.get("name")

            # Filter non-names
            if not source_name or source_name == 'モノローグ':
                continue

            if not speakers.get(source_name):
                speakers[source_name] = {
                    "source": source_name,
                    "text": "",
                    "block_idx": []
                }
            
            if name and not speakers[source_name].get("text"):
                speakers[source_name]["text"] = name
            
            speakers[source_name]["block_idx"].append(i)

        speakers = list(speakers.values())
        
        if not speakers:
            return
        
        before = copy.deepcopy(speakers)

        if focus_name:
            focus_name = self.loaded_chapter["data"][self.cur_open_block]["source_name"]
        
        dialog = story_speakers.Ui_story_speakers(speakers, focus_name)
        dialog.exec_()

        changed = False
        for i, speaker in enumerate(speakers):
            en_after = speaker["text"]
            en_before = before[i]["text"]
            if en_after != en_before:
                changed = True
                break
        
        if not changed:
            return
        
        # Apply changes
        for speaker_data in speakers:
            text = speaker_data["text"]
            block_idx = speaker_data["block_idx"]

            for idx in block_idx:
                block = self.loaded_chapter["data"][idx]
                block["name"] = text

        self.set_changed()
        self.set_timeout()
        self.reload_block()
    
    def goto_game(self):
        if not self.loaded_chapter:
            return
        
        if not self.cur_open_block:
            return
        
        id_list = []
        for block in self.loaded_chapter["data"][:self.cur_open_block + 1]:
            block_id = block.get("block_id", None)
            if block_id is not None:
                id_list.append(str(block_id))

        if not id_list:
            return
        
        out_str = "\n".join(id_list)

        util.write_carotenify_file(out_str, "gotoBlock")

    def handle_sync_change(self):
        if self.chkb_sync_game.isChecked():
            self.goto_game()
    

    def get_next_untranslated_block_index(self):
        if not self.loaded_chapter:
            return None

        if not self.cur_open_block:
            return None
        
        cur_index = self.cmb_textblock.currentIndex()
        index_list = list(range(len(self.box_items)))
        adjusted_list = index_list[cur_index + 1:] + index_list[:cur_index + 1]

        for i in adjusted_list:
            block_idx = self.box_items[i]
            block = self.loaded_chapter["data"][block_idx]
            if block.get("source") and not block.get("text"):
                return i
        
        return None

    def get_next_untranslated_choice_block_index(self):
        if not self.loaded_chapter:
            return None

        if not self.cur_open_block:
            return None
        
        cur_index = self.cmb_textblock.currentIndex()
        index_list = list(range(len(self.box_items)))
        adjusted_list = index_list[cur_index + 1:] + index_list[:cur_index + 1]

        for i in adjusted_list:
            block_idx = self.box_items[i]
            block = self.loaded_chapter["data"][block_idx]
            if block.get("choices"):
                for choice in block["choices"]:
                    if choice.get("source") and not choice.get("text"):
                        return i
                    
        return None
    
    def goto_next_untranslated_block(self):
        next_untranslated = self.get_next_untranslated_block_index()
        if next_untranslated is not None:
            self.cmb_textblock.setCurrentIndex(next_untranslated)
    
    def goto_next_untranslated_choice_block(self):
        next_untranslated = self.get_next_untranslated_choice_block_index()
        if next_untranslated is not None:
            self.cmb_textblock.setCurrentIndex(next_untranslated)
    
    def update_goto_buttons(self):
        next_untranslated = self.get_next_untranslated_block_index()
        next_untranslated_choice = self.get_next_untranslated_choice_block_index()

        self.btn_goto_choices.setEnabled(next_untranslated_choice is not None)
        self.btn_goto_dialogue.setEnabled(next_untranslated is not None)

    def recursive_find_all_child_stories(self, item, out_list):
        self.on_tree_item_expanded(item)
        for i in range(item.childCount()):
            child = item.child(i)
            if child.data(0, Qt.UserRole):
                self.recursive_find_all_child_stories(child, out_list)
            else:
                out_list.append(child)

    def context_goto_next_untranslated_block(self):
        """Finds all children of the current item and goes to the next untranslated block"""
        item = self.treeWidget.currentItem()

        if not item:
            return
        
        is_directory = item.data(0, Qt.UserRole)
        if not is_directory:
            return
        
        children = []
        self.recursive_find_all_child_stories(item, children)

        for child in children:
            file_path = child.data(0, Qt.UserRole + 1)
            if not file_path:
                continue
            chapter_data = util.load_json(file_path)
            for i, block in enumerate(chapter_data["data"]):
                if block.get("source") and not block.get("text"):
                    self.load_chapter(file_path, child)
                    index = self.box_items.index(i)
                    self.cmb_textblock.setCurrentIndex(index)
                    return
    
    def context_goto_next_untranslated_choice(self):
        """Finds all children of the current item and goes to the next untranslated choice block"""
        item = self.treeWidget.currentItem()

        if not item:
            return
        
        is_directory = item.data(0, Qt.UserRole)
        if not is_directory:
            return
        
        children = []
        self.recursive_find_all_child_stories(item, children)

        for child in children:
            file_path = child.data(0, Qt.UserRole + 1)
            if not file_path:
                continue
            chapter_data = util.load_json(file_path)
            for i, block in enumerate(chapter_data["data"]):
                if block.get("choices"):
                    for choice in block["choices"]:
                        if choice.get("source") and not choice.get("text"):
                            self.load_chapter(file_path, child)
                            index = self.box_items.index(i)
                            self.cmb_textblock.setCurrentIndex(index)
                            return

    
    def on_tree_context_menu(self, pos):
        item = self.treeWidget.currentItem()
        if not item:
            return
        
        is_directory = item.data(0, Qt.UserRole)

        menu = QMenu()
        action = menu.addAction("Open in Explorer" if is_directory else "Edit file")
        action.triggered.connect(lambda: util.open_path_in_explorer(item.data(0, Qt.UserRole + 1)))
        menu.addSeparator()
        action = menu.addAction("Goto next untranslated block")
        action.triggered.connect(self.context_goto_next_untranslated_block)
        action = menu.addAction("Goto next untranslated choice")
        action.triggered.connect(self.context_goto_next_untranslated_choice)

        menu.exec_(self.treeWidget.mapToGlobal(pos))


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
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.on_tree_context_menu)

        self.fill_branch(self.treeWidget, self.root_dir)
        self.fill_branch(self.treeWidget, util.ASSETS_FOLDER_EDITING + "home", home=True)


        self.treeWidget.setObjectName(u"treeWidget")
        self.treeWidget.setGeometry(QRect(10, 40, 251, 411))
        self.grp_actions = QGroupBox(story_editor)
        self.grp_actions.setObjectName(u"grp_actions")
        self.grp_actions.setGeometry(QRect(1059, 0, 211, 461))
        self.grp_actions.setTitle(u"Chapter Actions")
        self.btn_speakers = QPushButton(self.grp_actions)
        self.btn_speakers.setObjectName(u"btn_speakers")
        self.btn_speakers.setGeometry(QRect(10, 20, 191, 23))
        self.btn_speakers.setText(u"Manage speakers")
        self.btn_speakers.clicked.connect(self.manage_speakers)
        self.btn_goto_choices = QPushButton(self.grp_actions)
        self.btn_goto_choices.setObjectName(u"btn_goto_choices")
        self.btn_goto_choices.setGeometry(QRect(10, 80, 191, 23))
        self.btn_goto_choices.setText(u"Goto next untranslated choice")
        self.btn_goto_choices.setEnabled(False)
        self.btn_goto_choices.clicked.connect(self.goto_next_untranslated_choice_block)
        self.btn_goto_dialogue = QPushButton(self.grp_actions)
        self.btn_goto_dialogue.setObjectName(u"btn_goto_dialogue")
        self.btn_goto_dialogue.setGeometry(QRect(10, 50, 191, 23))
        self.btn_goto_dialogue.setText(u"Goto next untranslated dialogue")
        self.btn_goto_dialogue.setEnabled(False)
        self.btn_goto_dialogue.clicked.connect(self.goto_next_untranslated_block)


        self.txt_chapter_name = sutils.UmaPlainTextEdit(self.grp_actions)
        self.txt_chapter_name.setObjectName(u"textEdit_3")
        self.txt_chapter_name.setGeometry(QRect(10, 410, 191, 41))
        self.txt_chapter_name.setEnabled(True)
        self.txt_chapter_name.setReadOnly(False)
        self.txt_chapter_name.setLineWrapMode(sutils.UmaPlainTextEdit.NoWrap)
        self.txt_chapter_name.textChanged.connect(lambda: self.on_block_changed(self.txt_chapter_name))
        self.txt_chapter_name_source = sutils.UmaPlainTextEdit(self.grp_actions)
        self.txt_chapter_name_source.setObjectName(u"textEdit_4")
        self.txt_chapter_name_source.setGeometry(QRect(10, 360, 191, 41))
        self.txt_chapter_name_source.setReadOnly(True)
        self.lbl_chapter_title = QLabel(self.grp_actions)
        self.lbl_chapter_title.setObjectName(u"lbl_chapter_title")
        self.lbl_chapter_title.setGeometry(QRect(10, 340, 71, 16))
        self.lbl_chapter_title.setText(u"Chapter title")
        
        self.txt_source_name = sutils.UmaPlainTextEdit(story_editor)
        self.txt_source_name.setObjectName(u"txt_source_name")
        self.txt_source_name.setGeometry(QRect(270, 40, 401, 41))
        self.txt_source_name.setReadOnly(True)
        self.txt_source_name.setLineWrapMode(sutils.UmaPlainTextEdit.NoWrap)
        self.txt_source_name.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.txt_source_text = sutils.UmaPlainTextEdit(story_editor)
        self.txt_source_text.setObjectName(u"textEdit_5")
        self.txt_source_text.setGeometry(QRect(270, 90, 781, 121))
        self.txt_source_text.setReadOnly(True)
        self.txt_source_text.setLineWrapMode(sutils.UmaPlainTextEdit.NoWrap)
        
        self.txt_en_text = sutils.UmaPlainTextEdit(story_editor)
        self.txt_en_text.setObjectName(u"textEdit_6")
        self.txt_en_text.setGeometry(QRect(270, 280, 781, 121))
        self.txt_en_text.setLineWrapMode(sutils.UmaPlainTextEdit.NoWrap)
        self.txt_en_text.textChanged.connect(lambda: self.on_block_changed(self.txt_en_text))
        
        self.txt_en_name = sutils.UmaPlainTextEdit(story_editor)
        self.txt_en_name.setObjectName(u"txt_en_name")
        self.txt_en_name.setGeometry(QRect(270, 230, 401, 41))
        self.txt_en_name.setLineWrapMode(sutils.UmaPlainTextEdit.NoWrap)
        self.txt_en_name.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.txt_en_name.setReadOnly(True)
        self.txt_en_name.mouseReleaseEvent = self.speaker_clicked
        # self.txt_en_name.textChanged.connect(lambda: self.on_block_changed(self.txt_en_name))
        
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
        self.btn_next_block.setObjectName(u"btn_next_block")
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
        self.label_2.setText(u"Text block")
        self.chkb_autosave = QCheckBox(story_editor)
        self.chkb_autosave.setObjectName(u"chkb_autosave")
        self.chkb_autosave.setGeometry(QRect(960, 420, 81, 20))
        self.chkb_autosave.setText(u"Autosave")
        self.chkb_autosave.setChecked(settings.autosave_story_editor)
        self.chkb_autosave.stateChanged.connect(self.autosave_toggled)


        self.btn_save = QPushButton(story_editor)
        self.btn_save.setObjectName(u"btn_save")
        self.btn_save.setGeometry(QRect(954, 440, 91, 23))
        self.btn_save.setText(u"Save chapter")
        self.btn_save.clicked.connect(self.save_chapter)

        self.btn_choices = QPushButton(story_editor)
        self.btn_choices.setObjectName(u"btn_choices")
        self.btn_choices.setEnabled(False)
        self.btn_choices.setGeometry(QRect(960, 220, 91, 23))
        self.btn_choices.setText(u"Show choices")
        self.btn_choices.setEnabled(False)
        self.btn_choices.clicked.connect(self.choices_clicked)

        self.btn_apply_chapter = QPushButton(story_editor)
        self.btn_apply_chapter.setObjectName(u"btn_apply_chapter")
        self.btn_apply_chapter.setGeometry(QRect(810, 440, 131, 23))
        self.btn_apply_chapter.setText(u"Save && add to Hachimi")
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

        # self.btn_unpatch = QPushButton(story_editor)
        # self.btn_unpatch.setObjectName(u"btn_unpatch")
        # self.btn_unpatch.setGeometry(QRect(700, 440, 101, 23))
        # self.btn_unpatch.setText(u"Unpatch chapter")
        # self.btn_unpatch.clicked.connect(self.unpatch_chapter)

        self.lbl_length_marker = QLabel(story_editor)
        self.lbl_length_marker.setObjectName(u"lbl_length_marker")
        self.lbl_length_marker.setGeometry(QRect(1005, 281, 1, 119))
        self.lbl_length_marker.setAutoFillBackground(False)
        self.lbl_length_marker.setStyleSheet(u"background-color: rgb(255, 0, 0);")

        self.btn_goto_game = QPushButton(story_editor)
        self.btn_goto_game.setObjectName(u"btn_goto_game")
        self.btn_goto_game.setGeometry(QRect(710, 410, 75, 23))
        self.btn_goto_game.setText(u"Goto (Game)")
        self.btn_goto_game.clicked.connect(self.goto_game)

        self.chkb_sync_game = QCheckBox(story_editor)
        self.chkb_sync_game.setObjectName(u"chkb_sync_game")
        self.chkb_sync_game.setGeometry(QRect(790, 410, 81, 20))
        self.chkb_sync_game.setText(u"Auto-goto")
        self.chkb_sync_game.setChecked(False)
        self.chkb_sync_game.stateChanged.connect(self.handle_sync_change)
