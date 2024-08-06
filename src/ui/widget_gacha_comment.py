from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import glob
import util
from PIL import Image, ImageFilter, ImageQt
import json
import os
import ui.common as common

class Ui_gacha_comment(QWidget):
    def __init__(self, base_widget=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print("Setting up gacha comment widget")

        self.base_widget = base_widget

        self.changed = False

        self.img_data = get_img_data_dict()
        self.text_data = {}
        self.uma_font = common.uma_font(16)

        self.setupUi()
        self.setFixedSize(self.size())
    
    def setupUi(self):
        self.resize(1280, 720)
        self.setWindowTitle(u"Gacha Comments")
        self.verticalLayout_2 = QVBoxLayout(self)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 1100, 696))
        self.verticalLayout_5 = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")

        for key, data in self.img_data.items():
            grp_comment_container = QGroupBox(self.scrollAreaWidgetContents_2)
            grp_comment_container.setObjectName(u"grp_comment_container")
            grp_comment_container.setTitle(data['name'])

            horizontalLayout = QHBoxLayout(grp_comment_container)
            horizontalLayout.setObjectName(u"horizontalLayout")
            lbl_image = QLabel(grp_comment_container)
            lbl_image.setObjectName(u"lbl_image")
            lbl_image.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(data['image'])))

            lbl_image.setFixedWidth(650)
            lbl_image.setFixedHeight(163)
            lbl_image.setScaledContents(True)

            horizontalLayout.addWidget(lbl_image)

            txt_comment = QTextEdit(grp_comment_container)
            txt_comment.setObjectName(u"txt_comment")
            txt_comment.setPlainText(data['comment'])
            txt_comment.setFont(self.uma_font)
            txt_comment.setLineWrapMode(QTextEdit.NoWrap)
            
            cursor = txt_comment.textCursor()
            cursor.select(QTextCursor.Document)
            block_format = QTextBlockFormat()
            block_format.setAlignment(Qt.AlignCenter)
            cursor.mergeBlockFormat(block_format)

            txt_comment.textChanged.connect(self.set_changed)

            self.text_data[key] = txt_comment

            horizontalLayout.addWidget(txt_comment)


            self.verticalLayout_5.addWidget(grp_comment_container)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout_4.addWidget(self.scrollArea)


        self.horizontalLayout_2.addLayout(self.verticalLayout_4)

        self.grp_settings = QGroupBox(self)
        self.grp_settings.setObjectName(u"grp_settings")
        self.grp_settings.setMinimumSize(QSize(150, 0))
        self.grp_settings.setTitle(u"Settings")
        self.verticalLayout_3 = QVBoxLayout(self.grp_settings)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.btn_save = QPushButton(self.grp_settings)
        self.btn_save.setObjectName(u"btn_save")
        self.btn_save.setText(u"Save")
        self.btn_save.clicked.connect(self.save)

        self.verticalLayout_3.addWidget(self.btn_save)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)


        self.horizontalLayout_2.addWidget(self.grp_settings)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

    def set_changed(self):
        self.changed = True
        self.base_widget.set_changed(self)
        self.btn_save.setText("Save*")
    
    def set_unchanged(self):
        self.changed = False
        self.base_widget.set_unchanged(self)
        self.btn_save.setText("Save")
    
    def save(self):
        tl_data = {}
        for key, txt_comment in self.text_data.items():
            comment = txt_comment.toPlainText()
            if not comment:
                continue
            tl_data[key] = comment
        
        os.makedirs(os.path.dirname(util.GACHA_COMMENT_TL_PATH_EDITING), exist_ok=True)
        util.save_json(util.GACHA_COMMENT_TL_PATH_EDITING, tl_data)
        self.set_unchanged()
    
    def ask_close(self):
        return self.ask_save()

    def ask_save(self):
        if self.changed:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Question)
            msgbox.setText("You have unsaved changes. Do you want to save first?")
            msgbox.setWindowTitle("Gacha Comment Changes")
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msgbox.setDefaultButton(QMessageBox.Cancel)
            ret = msgbox.exec()

            if ret == QMessageBox.Cancel:
                return False
            
            if ret == QMessageBox.Yes:
                self.save()
            
            if ret == QMessageBox.No:
                self.set_unchanged()
        
        return True

def load_process_image(meta):
    texture_name = meta['file_name'].rsplit("/",1)[1]
    support_id = texture_name.rsplit("_",1)[1]
    file_path = util.ASSETS_FOLDER_EDITING + meta['file_name'] + "/" + texture_name + ".png"

    image = Image.open(file_path)
    image = image.split()[3]  # Get alpha channel only
    image = image.point(lambda a: 0 if a < 255 else 255)  # Convert to black and white

    # Scale image down 50%
    image = image.resize((image.width // 2, image.height // 2), Image.Resampling.BICUBIC)

    return (support_id, image)


def load_images():
    # Load all images.
    jsons = glob.glob(util.ASSETS_FOLDER_EDITING + "\\gacha\\comment\\**\\*.json")
    metas = []
    for file in jsons:
        data = util.load_json(file)
        metas.append(data)

    # TODO: Make this pooled map? Although it goes pretty fast on my machine.
    out = []
    for meta in metas:
        out.append(load_process_image(meta))
    
    return {k: v for k, v in out}


def get_img_data_dict():
    # Load gacha comment images as well as translations.
    img_data = load_images()

    # Load character and outfit names.
    chara_names = load_mdb_file("170")
    outfit_names = load_mdb_file("5")

    data_dict = {}
    for key, img in img_data.items():
        chara_name = chara_names.get(int(key[:4]), "???")
        outfit_name = outfit_names.get(int(key), "[???]")
        name = f"{chara_name} {outfit_name}"
        data_dict[key] = {
            'image': img,
            'name': name,
            'comment': ""
        }
    
    # Load translations.
    tl_path = util.GACHA_COMMENT_TL_PATH
    
    if os.path.exists(tl_path):
        tl_data = util.load_json(tl_path)
        for key, val in tl_data.items():
            data_dict[key]['comment'] = val

    return data_dict

def load_mdb_file(mdb_id):
    path = util.MDB_FOLDER_EDITING + f"\\text_data\\{mdb_id}.json"
    data = util.load_json(path)
    out = {}

    for entry in data:
        keys = json.loads(entry['keys'])
        out[keys[0][-1]] = entry['text']
    
    return out
