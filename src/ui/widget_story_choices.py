from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
import ui.common as common
import ui.widget_story_utils as sutils


class story_choice_dialog(QDialog):

    def __init__(self, choice_list, *args, **kwargs):
        self.text_widgets = []
        self.choice_list = choice_list
        super().__init__(*args, **kwargs)
        self.setupUi()
        self.setFixedSize(self.size())

    def on_text_changed(self):
        for i, widget in enumerate(self.text_widgets):
            text = sutils.get_text(widget)
            self.choice_list[i]['text'] = text


    def setupUi(self):
        if not self.objectName():
            self.setObjectName(u"Dialog")
        self.resize(584, 348)
        self.setWindowTitle("Story Choices")

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 547, 328))
        self.verticalLayout_4 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")


        for i, choice_data in enumerate(self.choice_list):
            grp_choice = QGroupBox(self.scrollAreaWidgetContents)
            grp_choice.setObjectName(f"grp_choice_{i}")
            grp_choice.setTitle(f"Choice {i + 1}")
            sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            sizePolicy1.setHorizontalStretch(0)
            sizePolicy1.setVerticalStretch(0)
            sizePolicy1.setHeightForWidth(grp_choice.sizePolicy().hasHeightForWidth())
            grp_choice.setSizePolicy(sizePolicy1)
            verticalLayout_2 = QVBoxLayout(grp_choice)
            verticalLayout_2.setObjectName(f"verticalLayout_2_{i}")
            txt_choice_source = QPlainTextEdit(grp_choice)
            txt_choice_source.setObjectName(f"txt_choice_source_{i}")
            sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            sizePolicy2.setHorizontalStretch(0)
            sizePolicy2.setVerticalStretch(0)
            sizePolicy2.setHeightForWidth(txt_choice_source.sizePolicy().hasHeightForWidth())
            txt_choice_source.setSizePolicy(sizePolicy2)
            txt_choice_source.setMaximumSize(QSize(16777215, 55))
            txt_choice_source.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            txt_choice_source.setFont(common.uma_font(16))
            txt_choice_source.setReadOnly(True)
            sutils.set_text(choice_data['source'], txt_choice_source)

            verticalLayout_2.addWidget(txt_choice_source)

            txt_choice_en = QPlainTextEdit(grp_choice)
            txt_choice_en.setObjectName(f"txt_choice_en_{i}")
            sizePolicy2.setHeightForWidth(txt_choice_en.sizePolicy().hasHeightForWidth())
            txt_choice_en.setSizePolicy(sizePolicy2)
            txt_choice_en.setMaximumSize(QSize(16777215, 55))
            txt_choice_en.setFont(common.uma_font(16))
            sutils.set_text(choice_data['text'], txt_choice_en)
            self.text_widgets.append(txt_choice_en)
            txt_choice_en.textChanged.connect(self.on_text_changed)

            verticalLayout_2.addWidget(txt_choice_en)


            self.verticalLayout_4.addWidget(grp_choice)

#         self.grp_choice_2 = QGroupBox(self.scrollAreaWidgetContents)
#         self.grp_choice_2.setObjectName(u"grp_choice_2")
#         sizePolicy1.setHeightForWidth(self.grp_choice_2.sizePolicy().hasHeightForWidth())
#         self.grp_choice_2.setSizePolicy(sizePolicy1)
#         self.verticalLayout_3 = QVBoxLayout(self.grp_choice_2)
#         self.verticalLayout_3.setObjectName(u"verticalLayout_3")
#         self.textEdit_3 = QTextEdit(self.grp_choice_2)
#         self.textEdit_3.setObjectName(u"textEdit_3")
#         sizePolicy2.setHeightForWidth(self.textEdit_3.sizePolicy().hasHeightForWidth())
#         self.textEdit_3.setSizePolicy(sizePolicy2)
#         self.textEdit_3.setMaximumSize(QSize(16777215, 55))
#         self.textEdit_3.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
#         self.textEdit_3.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
# "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
# "p, li { white-space: pre-wrap; }\n"
# "</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
# "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:16pt;\">test</span></p></body></html>")

#         self.verticalLayout_3.addWidget(self.textEdit_3)

#         self.textEdit_4 = QTextEdit(self.grp_choice_2)
#         self.textEdit_4.setObjectName(u"textEdit_4")
#         sizePolicy2.setHeightForWidth(self.textEdit_4.sizePolicy().hasHeightForWidth())
#         self.textEdit_4.setSizePolicy(sizePolicy2)
#         self.textEdit_4.setMaximumSize(QSize(16777215, 55))
#         self.textEdit_4.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
# "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
# "p, li { white-space: pre-wrap; }\n"
# "</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
# "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")

#         self.verticalLayout_3.addWidget(self.textEdit_4)


#         self.verticalLayout_4.addWidget(self.grp_choice_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)


