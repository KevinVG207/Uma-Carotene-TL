from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import ui.common as common
import ui.widget_story_utils as sutils
import util
import os
import copy

def generate_autofill_dict():
    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "170.json")
    data = util.load_json(path)

    autofill_dict = copy.deepcopy(common.SPEAKER_AUTOFILL)

    for entry in data:
        if not entry.get("text"):
            return
        
        text = entry["text"]
        source = entry["source"]
        autofill_dict[source] = text
    
    return autofill_dict

class Ui_story_speakers(QDialog):
    autofill_dict = generate_autofill_dict()

    def __init__(self, speakers_list, focus_name, *args, **kwargs):
        self.text_widgets = []
        self.speakers_list = speakers_list
        self.focus_name = focus_name
        super().__init__(*args, **kwargs)
        self.setupUi()
        self.setFixedSize(self.size())

        if self.focus_name:
            for i, speaker_data in enumerate(self.speakers_list):
                if speaker_data['source'] == self.focus_name:
                    self.text_widgets[i].setStyleSheet("border: 1px solid red;")
                    if i > 2:
                        self.scrollArea.ensureWidgetVisible(self.text_widgets[i])
                    break
    
    def on_text_changed(self):
        for i, widget in enumerate(self.text_widgets):
            text = sutils.get_text(widget)
            self.speakers_list[i]['text'] = text

    def on_autofill(self):
        for i, speaker_data in enumerate(self.speakers_list):
            source = speaker_data['source']
            if source in self.autofill_dict:
                sutils.set_text(self.autofill_dict[source], self.text_widgets[i])

    def setupUi(self):
        if not self.objectName():
            self.setObjectName(u"widget_story_speakers")
        self.resize(476, 480)
        self.setWindowTitle(u"Manage Speakers")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.verticalLayout_2 = QVBoxLayout(self)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 439, 460))
        self.verticalLayout_4 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btn_autofill = QPushButton(self.scrollAreaWidgetContents)
        self.btn_autofill.setObjectName(u"btn_autofill")
        self.btn_autofill.setText("Autofill")
        self.btn_autofill.clicked.connect(self.on_autofill)

        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_autofill.sizePolicy().hasHeightForWidth())
        self.btn_autofill.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.btn_autofill)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        for i, speaker_data in enumerate(self.speakers_list):
            grp_speaker = QGroupBox(self.scrollAreaWidgetContents)
            grp_speaker.setObjectName(f"grp_speaker_{i}")
            grp_speaker.setTitle(f"Speaker {i + 1}")
            verticalLayout = QVBoxLayout(grp_speaker)
            verticalLayout.setObjectName(f"verticalLayout_{i}")
            txt_source = sutils.UmaPlainTextEdit(grp_speaker)
            txt_source.setObjectName(f"txt_source_{i}")
            sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            sizePolicy1.setHorizontalStretch(0)
            sizePolicy1.setVerticalStretch(0)
            sizePolicy1.setHeightForWidth(txt_source.sizePolicy().hasHeightForWidth())
            txt_source.setSizePolicy(sizePolicy1)
            txt_source.setMaximumSize(QSize(401, 41))
            txt_source.setFont(common.uma_font(16))
            txt_source.setReadOnly(True)
            txt_source.setLineWrapMode(sutils.UmaPlainTextEdit.NoWrap)
            txt_source.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sutils.set_text(speaker_data['source'], txt_source)

            verticalLayout.addWidget(txt_source)

            txt_en = sutils.UmaPlainTextEdit(grp_speaker)
            txt_en.setObjectName(f"txt_en_{i}")
            sizePolicy1.setHeightForWidth(txt_en.sizePolicy().hasHeightForWidth())
            txt_en.setSizePolicy(sizePolicy1)
            txt_en.setMaximumSize(QSize(401, 41))
            txt_en.setFont(common.uma_font(16))
            txt_en.setLineWrapMode(sutils.UmaPlainTextEdit.NoWrap)
            txt_en.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sutils.set_text(speaker_data['text'], txt_en)
            self.text_widgets.append(txt_en)
            txt_en.textChanged.connect(self.on_text_changed)

            verticalLayout.addWidget(txt_en)

            self.verticalLayout_4.addWidget(grp_speaker)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_2.addWidget(self.scrollArea)


