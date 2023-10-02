from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import ui.widget_tabs as widget_tabs

def main():
    app = QApplication([])
    widget = widget_tabs.Ui_widget_tabs()
    widget.show()
    app.exec_()
    pass

if __name__ == "__main__":
    main()
