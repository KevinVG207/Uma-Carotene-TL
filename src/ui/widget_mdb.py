from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ui.common import *
import intermediate
import util
import tqdm
import re

class Ui_widget_mdb(QWidget):
    def __init__(self, *args, base_widget=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setFixedSize(self.size())

        self.base_widget = base_widget

        self.tab_text_org = None

        self.current_json = None
        self.current_data = None

        self.filter_timer = QTimer()

        self.set_unchanged()

    def set_changed(self):
        self.changed = True
        self.base_widget.set_changed(self)
    
    def set_unchanged(self):
        self.changed = False
        self.base_widget.set_unchanged(self)

    def ask_close(self):
        return self.ask_save()
    
    def ask_save(self):
        if self.changed:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Question)
            msgbox.setText("You have unsaved MDB changes. Do you want to save first?")
            msgbox.setWindowTitle("MDB Changes")
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msgbox.setDefaultButton(QMessageBox.Cancel)
            ret = msgbox.exec()

            if ret == QMessageBox.Cancel:
                return False
            
            if ret == QMessageBox.Yes:
                self.save(force=True)
        
        return True


    def fill_tree_categories(self):
        self.tree_categories.clear()

        categories = intermediate.get_mdb_structure()

        def recursive_add_categories(parent, categories, history):
            for category in sorted(categories.keys(), key=util.strings_numeric_key):
                if isinstance(categories[category], dict):
                    item = QTreeWidgetItem(parent)
                    item.setText(0, category)
                    history.append(category)
                    recursive_add_categories(item, categories[category], history)
                    history.pop()
                else:
                    # Leaf
                    item = QTreeWidgetItem(parent)

                    suffix = ""
                    cur_dict = get_mdb_cat_names()
                    for cat in history:
                        if cat in cur_dict:
                            cur_dict = cur_dict[cat]
                    
                    if cur_dict.get(category):
                        suffix = f" {cur_dict[category]}"

                    item.setText(0, category + suffix)
                    item.setData(0, Qt.UserRole, categories[category])
        
        recursive_add_categories(self.tree_categories, categories, [])


    def update_text(self, txt):
        txt.size_change()

    def save(self, force=False):
        if not self.current_data:
            return

        if not self.changed:
            return
        
        if not force:
            # Ask for confirmation
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Question)
            msgbox.setText("Are you sure you want to save?")
            msgbox.setWindowTitle("Save")
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgbox.setDefaultButton(QMessageBox.No)
            ret = msgbox.exec()

            if ret != QMessageBox.Yes:
                return
        
        # Save
        cur_data = self.current_data
        for i, entry in enumerate(cur_data):
            cur_grp_box = self.verticalLayout.itemAt(i).widget()
            cur_txt_translation = cur_grp_box.findChild(QTextEdit, "txt_translation")
            cur_translation = cur_txt_translation.toPlainText().replace('\r', '\\r').replace('\n', '\\n')
            cur_txt_source = cur_grp_box.findChild(QTextEdit, "txt_source")
            cur_source = cur_txt_source.toPlainText().replace('\r', '\\r').replace('\n', '\\n')

            # Sanity check
            if entry['source'] != cur_source:
                raise Exception(f"Source mismatch: {entry['source']} != {cur_source}")

            if entry['text'] != cur_translation:
                entry['prev'] = entry['text']
                entry['text'] = cur_translation
                entry['new'] = False
                entry['edited'] = False

        util.save_json(self.current_json, cur_data)
        self.set_unchanged()


    def reload(self):
        if not self.current_json:
            return
        
        # Ask for confirmation
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Question)
        msgbox.setText("Are you sure you want to discard all changes?")
        msgbox.setWindowTitle("Reload")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        ret = msgbox.exec()

        if ret != QMessageBox.Yes:
            return

        self.fill_tl_entries(self.current_json, keep_position=True)

    def _filter(self):
        if not self.current_data:
            return

        search_term = self.le_searchbar.text().lower()


        if self.chk_exact_filter.isChecked():
            for i in range(self.verticalLayout.count()):
                cur_grp_box = self.verticalLayout.itemAt(i).widget()
                cur_txt_translation = cur_grp_box.findChild(QTextEdit, "txt_translation")
                cur_txt_source = cur_grp_box.findChild(QTextEdit, "txt_source")

                cur_translation = cur_txt_translation.toPlainText().lower()
                cur_source = cur_txt_source.toPlainText().lower()

                cur_grp_box.hide()

                if self.chk_en_filter.isChecked() and search_term == cur_translation:
                    cur_grp_box.show()
                
                if self.chk_jp_filter.isChecked() and search_term == cur_source:
                    cur_grp_box.show()
            return


        if not search_term:
            for i in range(self.verticalLayout.count()):
                cur_grp_box = self.verticalLayout.itemAt(i).widget()
                cur_grp_box.show()
            return

        for i in range(self.verticalLayout.count()):
            cur_grp_box = self.verticalLayout.itemAt(i).widget()
            cur_txt_translation = cur_grp_box.findChild(QTextEdit, "txt_translation")
            cur_txt_source = cur_grp_box.findChild(QTextEdit, "txt_source")

            cur_translation = cur_txt_translation.toPlainText().lower()
            cur_source = cur_txt_source.toPlainText().lower()

            cur_grp_box.hide()

            if self.chk_en_filter.isChecked() and search_term in cur_translation:
                cur_grp_box.show()
                
            if self.chk_jp_filter.isChecked() and search_term in cur_source:
                cur_grp_box.show()
            
            # Regex search
            if self.chk_en_filter.isChecked() and re.search(search_term, cur_translation):
                cur_grp_box.show()
            
            if self.chk_jp_filter.isChecked() and re.search(search_term, cur_source):
                cur_grp_box.show()

    def filter(self):
        # Debounce
        self.filter_timer.stop()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self._filter)
        self.filter_timer.start(250)


    def fill_tl_entries(self, json_path, keep_position=False):
        if self.current_json == json_path:
            return
        
        if self.changed:
            # Ask for confirmation
            # Yes, No, Cancel
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Question)
            msgbox.setText("You have unsaved changes. Do you want to save first?")
            msgbox.setWindowTitle("Unsaved Changes")
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msgbox.setDefaultButton(QMessageBox.Cancel)
            ret = msgbox.exec()

            if ret == QMessageBox.Cancel:
                return
            
            if ret == QMessageBox.Yes:
                self.save(force=True)

        self.current_json = json_path
        self.current_data = util.load_json(json_path)

        scroll_position = 0
        if keep_position:
            scroll_position = self.scrollArea.verticalScrollBar().value()

        while self.verticalLayout.count():
            child = self.verticalLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for entry in tqdm.tqdm(self.current_data, desc="Loading TL Entries"):
            keys = entry['keys']
            source = entry['source'].replace('\\r', '\r').replace('\\n', '\n')
            text = entry['text'].replace('\\r', '\r').replace('\\n', '\n')
            font = uma_font(16)
            spacing = -16

            grp_tl_entry = QGroupBox(self.scrollAreaWidgetContents)
            grp_tl_entry.setObjectName(f"grp_tl_entry_{keys}")
            grp_tl_entry.setEnabled(True)
            sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            sizePolicy1.setHorizontalStretch(0)
            sizePolicy1.setVerticalStretch(0)
            sizePolicy1.setHeightForWidth(grp_tl_entry.sizePolicy().hasHeightForWidth())
            grp_tl_entry.setSizePolicy(sizePolicy1)
            grp_tl_entry.setMinimumSize(QSize(0, 0))
            grp_tl_entry.setMaximumWidth(821)
            grp_tl_entry.setTitle(keys)
            verticalLayout_2 = QVBoxLayout(grp_tl_entry)
            verticalLayout_2.setObjectName(u"verticalLayout_2")
            horizontalLayout = QHBoxLayout()
            horizontalLayout.setObjectName(u"horizontalLayout")
            lbl_japanese = QLabel(grp_tl_entry)
            lbl_japanese.setObjectName(u"lbl_japanese")
            sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
            sizePolicy2.setHorizontalStretch(0)
            sizePolicy2.setVerticalStretch(0)
            sizePolicy2.setHeightForWidth(lbl_japanese.sizePolicy().hasHeightForWidth())
            lbl_japanese.setSizePolicy(sizePolicy2)
            lbl_japanese.setMinimumSize(QSize(50, 0))
            lbl_japanese.setText(u"Japanese")
            lbl_japanese.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

            horizontalLayout.addWidget(lbl_japanese)

            txt_source = ExpandingTextEdit(grp_tl_entry)
            txt_source.setObjectName(u"txt_source")
            sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            sizePolicy3.setHorizontalStretch(0)
            sizePolicy3.setVerticalStretch(0)
            sizePolicy3.setHeightForWidth(txt_source.sizePolicy().hasHeightForWidth())
            txt_source.setSizePolicy(sizePolicy3)
            txt_source.setMinimumSize(QSize(0, 0))
            txt_source.setMaximumSize(QSize(16777215, 23))
            txt_source.setReadOnly(True)
            txt_source.setLineWrapMode(QTextEdit.NoWrap)
            txt_source.setFont(font)
            txt_source.textChanged.connect(lambda: self.update_text(txt_source))
            txt_source.setText(source)

            # txt_source.line_spacing(spacing)

            horizontalLayout.addWidget(txt_source)


            verticalLayout_2.addLayout(horizontalLayout)

            horizontalLayout_2 = QHBoxLayout()
            horizontalLayout_2.setObjectName(u"horizontalLayout_2")
            lbl_english = QLabel(grp_tl_entry)
            lbl_english.setObjectName(u"lbl_english")
            sizePolicy2.setHeightForWidth(lbl_english.sizePolicy().hasHeightForWidth())
            lbl_english.setSizePolicy(sizePolicy2)
            lbl_english.setMinimumSize(QSize(50, 0))
            lbl_english.setText(u"English")
            lbl_english.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

            horizontalLayout_2.addWidget(lbl_english)

            txt_translation = ExpandingTextEdit(grp_tl_entry)
            txt_translation.setObjectName(u"txt_translation")
            sizePolicy3.setHeightForWidth(txt_translation.sizePolicy().hasHeightForWidth())
            txt_translation.setSizePolicy(sizePolicy3)
            txt_translation.setMinimumSize(QSize(0, 0))
            txt_translation.setMaximumSize(QSize(16777215, 23))
            txt_translation.setLineWrapMode(QTextEdit.NoWrap)
            txt_translation.setFont(font)

            txt_translation.textChanged.connect(lambda: self.update_text(txt_translation))
            txt_translation.textChanged.connect(self.set_changed)

            txt_translation.setText(text)
            # txt_translation.line_spacing(spacing)

            horizontalLayout_2.addWidget(txt_translation)


            verticalLayout_2.addLayout(horizontalLayout_2)

            self.verticalLayout.addWidget(grp_tl_entry)


        # self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Minimum)
        # self.verticalLayout.addItem(self.verticalSpacer)
        self.scrollArea.verticalScrollBar().setValue(scroll_position)
        self.set_unchanged()

    def setupUi(self, widget_mdb):
        if not widget_mdb.objectName():
            widget_mdb.setObjectName(u"widget_mdb")
        widget_mdb.resize(1280, 720)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_mdb.sizePolicy().hasHeightForWidth())
        widget_mdb.setSizePolicy(sizePolicy)
        widget_mdb.setMinimumSize(QSize(1280, 720))
        widget_mdb.setWindowTitle(u"MDB Widget")
        self.tree_categories = QTreeWidget(widget_mdb)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"Root")
        self.tree_categories.setHeaderItem(__qtreewidgetitem)
        self.tree_categories.setHeaderHidden(True)
        self.tree_categories.setObjectName(u"tree_categories")
        self.tree_categories.setGeometry(QRect(10, 40, 231, 671))
        self.tree_categories.setAlternatingRowColors(True)
        self.tree_categories.itemClicked.connect(lambda item, column: self.fill_tl_entries(item.data(0, Qt.UserRole)) if item.data(0, Qt.UserRole) else None)

        self.fill_tree_categories()

        self.lbl_category = QLabel(widget_mdb)
        self.lbl_category.setObjectName(u"lbl_category")
        self.lbl_category.setGeometry(QRect(10, 10, 231, 21))
        self.lbl_category.setText(u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Choose Category</span></p></body></html>")
        self.scrollArea = QScrollArea(widget_mdb)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(QRect(250, 40, 861, 671))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 859, 669))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.grp_actions = QGroupBox(widget_mdb)
        self.grp_actions.setObjectName(u"grp_actions")
        self.grp_actions.setGeometry(QRect(1120, 10, 151, 701))
        self.grp_actions.setTitle(u"Actions")


        self.btn_save = QPushButton(self.grp_actions)
        self.btn_save.setObjectName(u"btn_save")
        self.btn_save.setGeometry(QRect(10, 20, 131, 23))
        self.btn_save.setText(u"Save")
        self.btn_save.clicked.connect(self.save)
        self.btn_reload = QPushButton(self.grp_actions)
        self.btn_reload.setObjectName(u"btn_reload")
        self.btn_reload.setGeometry(QRect(10, 50, 131, 23))
        self.btn_reload.setText(u"Discard Changes")
        self.btn_reload.clicked.connect(self.reload)

        self.le_searchbar = QLineEdit(widget_mdb)
        self.le_searchbar.setObjectName(u"le_searchbar")
        self.le_searchbar.setGeometry(QRect(290, 8, 671, 24))
        font = QFont()
        font.setPointSize(10)
        self.le_searchbar.setFont(font)
        self.lbl_search = QLabel(widget_mdb)
        self.lbl_search.setObjectName(u"lbl_search")
        self.lbl_search.setGeometry(QRect(250, 10, 41, 21))
        self.lbl_search.setText(u"Search:")
        self.chk_exact_filter = QCheckBox(widget_mdb)
        self.chk_exact_filter.setObjectName(u"chk_exact_filter")
        self.chk_exact_filter.setGeometry(QRect(1049, 10, 61, 20))
        self.chk_exact_filter.setText(u"Exact")
        self.chk_en_filter = QCheckBox(widget_mdb)
        self.chk_en_filter.setObjectName(u"chk_en_filter")
        self.chk_en_filter.setGeometry(QRect(1010, 10, 41, 20))
        self.chk_en_filter.setText(u"EN")
        self.chk_en_filter.setChecked(True)
        self.chk_jp_filter = QCheckBox(widget_mdb)
        self.chk_jp_filter.setObjectName(u"chk_jp_filter")
        self.chk_jp_filter.setGeometry(QRect(970, 10, 41, 20))
        self.chk_jp_filter.setText(u"JP")
        self.chk_jp_filter.setChecked(True)


        self.le_searchbar.textChanged.connect(self.filter)
        self.chk_exact_filter.stateChanged.connect(self.filter)
        self.chk_en_filter.stateChanged.connect(self.filter)
        self.chk_jp_filter.stateChanged.connect(self.filter)


        self.retranslateUi(widget_mdb)

        QMetaObject.connectSlotsByName(widget_mdb)
    # setupUi

    def retranslateUi(self, widget_mdb):
        pass
    # retranslateUi

