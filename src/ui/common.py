from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import math

class ExpandingTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document().contentsChanged.connect(self.size_change)

        self.height_min = 23
        self.height_max = 65000
    
    def size_change(self):
        doc_height = math.ceil(self.document().size().height()) + 2
        if self.height_min <= doc_height <= self.height_max:
            print(doc_height)
            self.setMinimumHeight(doc_height)
            self.setMaximumHeight(doc_height)