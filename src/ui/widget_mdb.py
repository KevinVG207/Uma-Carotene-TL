from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ui.common import *

class Ui_widget_mdb(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setFixedSize(self.size())

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
        __qtreewidgetitem.setText(0, u"1");
        self.tree_categories.setHeaderItem(__qtreewidgetitem)
        self.tree_categories.setObjectName(u"tree_categories")
        self.tree_categories.setGeometry(QRect(10, 40, 231, 671))
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
        self.grp_tl_entry = QGroupBox(self.scrollAreaWidgetContents)
        self.grp_tl_entry.setObjectName(u"grp_tl_entry")
        self.grp_tl_entry.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.grp_tl_entry.sizePolicy().hasHeightForWidth())
        self.grp_tl_entry.setSizePolicy(sizePolicy1)
        self.grp_tl_entry.setMinimumSize(QSize(0, 0))
        self.grp_tl_entry.setTitle(u"TEXTID")
        self.verticalLayout_2 = QVBoxLayout(self.grp_tl_entry)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lbl_japanese = QLabel(self.grp_tl_entry)
        self.lbl_japanese.setObjectName(u"lbl_japanese")
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lbl_japanese.sizePolicy().hasHeightForWidth())
        self.lbl_japanese.setSizePolicy(sizePolicy2)
        self.lbl_japanese.setMinimumSize(QSize(50, 0))
        self.lbl_japanese.setText(u"Japanese")
        self.lbl_japanese.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.horizontalLayout.addWidget(self.lbl_japanese)

        self.txt_source = ExpandingTextEdit(self.grp_tl_entry)
        self.txt_source.setObjectName(u"txt_source")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.txt_source.sizePolicy().hasHeightForWidth())
        self.txt_source.setSizePolicy(sizePolicy3)
        self.txt_source.setMinimumSize(QSize(0, 0))
        self.txt_source.setMaximumSize(QSize(16777215, 23))
        self.txt_source.setReadOnly(True)

        self.horizontalLayout.addWidget(self.txt_source)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lbl_english = QLabel(self.grp_tl_entry)
        self.lbl_english.setObjectName(u"lbl_english")
        sizePolicy2.setHeightForWidth(self.lbl_english.sizePolicy().hasHeightForWidth())
        self.lbl_english.setSizePolicy(sizePolicy2)
        self.lbl_english.setMinimumSize(QSize(50, 0))
        self.lbl_english.setText(u"English")
        self.lbl_english.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.horizontalLayout_2.addWidget(self.lbl_english)

        self.txt_translation = ExpandingTextEdit(self.grp_tl_entry)
        self.txt_translation.setObjectName(u"txt_translation")
        sizePolicy3.setHeightForWidth(self.txt_translation.sizePolicy().hasHeightForWidth())
        self.txt_translation.setSizePolicy(sizePolicy3)
        self.txt_translation.setMinimumSize(QSize(0, 0))
        self.txt_translation.setMaximumSize(QSize(16777215, 23))

        self.horizontalLayout_2.addWidget(self.txt_translation)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.verticalLayout.addWidget(self.grp_tl_entry)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.grp_actions = QGroupBox(widget_mdb)
        self.grp_actions.setObjectName(u"grp_actions")
        self.grp_actions.setGeometry(QRect(1120, 10, 151, 701))
        self.grp_actions.setTitle(u"Actions")
        self.le_searchbar = QLineEdit(widget_mdb)
        self.le_searchbar.setObjectName(u"le_searchbar")
        self.le_searchbar.setGeometry(QRect(290, 10, 821, 20))
        self.lbl_search = QLabel(widget_mdb)
        self.lbl_search.setObjectName(u"lbl_search")
        self.lbl_search.setGeometry(QRect(250, 10, 41, 21))
        self.lbl_search.setText(u"Search:")

        self.retranslateUi(widget_mdb)

        QMetaObject.connectSlotsByName(widget_mdb)
    # setupUi

    def retranslateUi(self, widget_mdb):
        pass
    # retranslateUi

