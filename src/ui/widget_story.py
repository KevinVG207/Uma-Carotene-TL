from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
import util
import os
import json

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

        self.chara_name_dict = {}
        json_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "6.json")
        chara_name_data = util.load_json(json_path)
        for entry in chara_name_data:
            if not entry.get("text"):
                continue
            char_id = json.loads(entry["keys"])[0][1]
            self.chara_name_dict[str(char_id)] = entry["text"]

        self.setupUi(self)
        self.setFixedSize(self.size())
    
    def set_changed(self):
        self.changed = True
        self.base_widget.set_changed(self)
    
    def set_unchanged(self):
        self.changed = False
        self.base_widget.set_unchanged(self)

    def fill_branch(self, parent, path, breadcrumb=[]):
        # Add files/paths to the tree
        # First, delete any existing children
        if isinstance(parent, QTreeWidgetItem):
            parent.takeChildren()

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

    
    def load_chapter(self, file_path):
        pass


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
        self.pushButton = QPushButton(story_editor)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(10, 10, 75, 23))
        self.pushButton.setText(u"<- Prev")
        self.pushButton_2 = QPushButton(story_editor)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(180, 10, 75, 23))
        self.pushButton_2.setText(u"Next ->")
        self.treeWidget = QTreeWidget(story_editor)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"Story Chapter")
        self.treeWidget.setHeaderItem(__qtreewidgetitem)
        # self.treeWidget.itemClicked.connect(self.on_tree_item_clicked)
        self.treeWidget.itemExpanded.connect(self.on_tree_item_expanded)

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
        self.textEdit = QTextEdit(story_editor)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(270, 40, 401, 41))
        self.textEdit.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.textEdit_5 = QTextEdit(story_editor)
        self.textEdit_5.setObjectName(u"textEdit_5")
        self.textEdit_5.setGeometry(QRect(270, 90, 781, 121))
        self.textEdit_5.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.textEdit_6 = QTextEdit(story_editor)
        self.textEdit_6.setObjectName(u"textEdit_6")
        self.textEdit_6.setGeometry(QRect(270, 280, 781, 121))
        self.textEdit_6.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.textEdit_2 = QTextEdit(story_editor)
        self.textEdit_2.setObjectName(u"textEdit_2")
        self.textEdit_2.setGeometry(QRect(270, 230, 401, 41))
        self.textEdit_2.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.comboBox = QComboBox(story_editor)
        self.comboBox.addItem(u"New Item")
        self.comboBox.addItem(u"New Item")
        self.comboBox.addItem(u"New Item")
        self.comboBox.addItem(u"New Item")
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(270, 410, 271, 22))
        self.pushButton_3 = QPushButton(story_editor)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setGeometry(QRect(550, 410, 75, 23))
        self.pushButton_3.setText(u"<- Prev")
        self.pushButton_4 = QPushButton(story_editor)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setGeometry(QRect(630, 410, 75, 23))
        self.pushButton_4.setText(u"Next ->")
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
        self.pushButton_8 = QPushButton(story_editor)
        self.pushButton_8.setObjectName(u"pushButton_8")
        self.pushButton_8.setGeometry(QRect(954, 510, 91, 23))
        self.pushButton_8.setText(u"Save chapter")
        self.pushButton_11 = QPushButton(story_editor)
        self.pushButton_11.setObjectName(u"pushButton_11")
        self.pushButton_11.setEnabled(False)
        self.pushButton_11.setGeometry(QRect(874, 220, 91, 23))
        self.pushButton_11.setText(u"Show choices")
        self.pushButton_12 = QPushButton(story_editor)
        self.pushButton_12.setObjectName(u"pushButton_12")
        self.pushButton_12.setGeometry(QRect(270, 510, 101, 23))
        self.pushButton_12.setText(u"Discard changes")

