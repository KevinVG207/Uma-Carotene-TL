from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget

class Ui_widget_main(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setFixedSize(self.size())

    def setupUi(self, widget_main):
        if not widget_main.objectName():
            widget_main.setObjectName(u"widget_main")
        widget_main.resize(401, 349)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(widget_main.sizePolicy().hasHeightForWidth())
        widget_main.setSizePolicy(sizePolicy)
        widget_main.setMinimumSize(QSize(401, 349))
        widget_main.setWindowTitle(u"Widget Main")
        widget_main.setLayoutDirection(Qt.LeftToRight)
        self.lbl_patch_status_indicator = QLabel(widget_main)
        self.lbl_patch_status_indicator.setObjectName(u"lbl_patch_status_indicator")
        self.lbl_patch_status_indicator.setGeometry(QRect(110, 120, 21, 20))
        sizePolicy.setHeightForWidth(self.lbl_patch_status_indicator.sizePolicy().hasHeightForWidth())
        self.lbl_patch_status_indicator.setSizePolicy(sizePolicy)
        self.lbl_patch_status_indicator.setMinimumSize(QSize(20, 20))
        self.lbl_patch_status_indicator.setStyleSheet(u"background-color: rgb(255, 106, 0);")
        self.lbl_patch_status_indicator.setText(u"")
        self.lbl_patch_status_2 = QLabel(widget_main)
        self.lbl_patch_status_2.setObjectName(u"lbl_patch_status_2")
        self.lbl_patch_status_2.setGeometry(QRect(140, 120, 151, 21))
        self.lbl_patch_status_2.setText(u"Unpatched")
        self.lbl_contribute = QLabel(widget_main)
        self.lbl_contribute.setObjectName(u"lbl_contribute")
        self.lbl_contribute.setGeometry(QRect(110, 210, 181, 21))
        self.lbl_contribute.setText(u"Contribute")
        self.lbl_contribute.setAlignment(Qt.AlignCenter)
        self.btn_revert = QPushButton(widget_main)
        self.btn_revert.setObjectName(u"btn_revert")
        self.btn_revert.setGeometry(QRect(210, 150, 83, 31))
        self.btn_revert.setText(u"Revert")
        self.btn_patch = QPushButton(widget_main)
        self.btn_patch.setObjectName(u"btn_patch")
        self.btn_patch.setGeometry(QRect(110, 150, 83, 31))
        self.btn_patch.setText(u"Patch")
        self.lbl_update_indicator = QLabel(widget_main)
        self.lbl_update_indicator.setObjectName(u"lbl_update_indicator")
        self.lbl_update_indicator.setGeometry(QRect(110, 30, 20, 21))
        sizePolicy.setHeightForWidth(self.lbl_update_indicator.sizePolicy().hasHeightForWidth())
        self.lbl_update_indicator.setSizePolicy(sizePolicy)
        self.lbl_update_indicator.setMinimumSize(QSize(20, 20))
        self.lbl_update_indicator.setStyleSheet(u"background-color: rgb(255, 0, 0);")
        self.lbl_update_indicator.setText(u"")
        self.lbl_update_text = QLabel(widget_main)
        self.lbl_update_text.setObjectName(u"lbl_update_text")
        self.lbl_update_text.setGeometry(QRect(140, 30, 142, 20))
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbl_update_text.sizePolicy().hasHeightForWidth())
        self.lbl_update_text.setSizePolicy(sizePolicy1)
        self.lbl_update_text.setText(u"No update available")
        self.btn_commit = QPushButton(widget_main)
        self.btn_commit.setObjectName(u"btn_commit")
        self.btn_commit.setGeometry(QRect(220, 240, 81, 31))
        self.btn_commit.setText(u"Commit Edits")
        self.btn_update = QPushButton(widget_main)
        self.btn_update.setObjectName(u"btn_update")
        self.btn_update.setGeometry(QRect(110, 60, 81, 31))
        self.btn_update.setText(u"Update")
        self.btn_index = QPushButton(widget_main)
        self.btn_index.setObjectName(u"btn_index")
        self.btn_index.setGeometry(QRect(100, 240, 101, 31))
        self.btn_index.setText(u"Index Game Text")
        self.line = QFrame(widget_main)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(100, 200, 201, 16))
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.retranslateUi(widget_main)

        QMetaObject.connectSlotsByName(widget_main)
    # setupUi

    def retranslateUi(self, widget_main):
        pass
    # retranslateUi

