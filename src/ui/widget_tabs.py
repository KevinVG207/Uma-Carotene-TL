from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
import ui.widget_main as widget_main
import ui.widget_mdb as widget_mdb

class Ui_widget_tabs(QWidget):
    def __init__(self, app, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.app = app

        self.setupUi(self)
        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.adjust_size()
    
    def set_changed(self, widget: QWidget) -> None:
        # Add * to tab name
        index = self.tabWidget.indexOf(widget)
        cur_tab_text = self.tabWidget.tabText(index)
        if not cur_tab_text.endswith("*"):
            self.tabWidget.setTabText(index, cur_tab_text + "*")

    def set_unchanged(self, widget: QWidget) -> None:
        # Remove * from tab name
        index = self.tabWidget.indexOf(widget)
        cur_tab_text = self.tabWidget.tabText(index)
        if cur_tab_text.endswith("*"):
            self.tabWidget.setTabText(index, cur_tab_text[:-1])

    def tab_changed(self, index: int) -> None:
        # Change size of window to fit the tab
        self.adjust_size()

    def adjust_size(self) -> None:
        current_tab = self.tabWidget.currentWidget()
        current_size = current_tab.size()

        # Add offsets on all sides
        current_size.setWidth(current_size.width() + 28)
        current_size.setHeight(current_size.height() + 48)

        print(current_size)
        self.setFixedSize(current_size)
    
    # def close(self) -> bool:
    #     for i in range(self.tabWidget.count()):
    #         widget = self.tabWidget.widget(i)
    #         # Check if it has ask_close() method
    #         if hasattr(widget, "ask_close"):
    #             # If it does, call it
    #             if not widget.ask_close():
    #                 return False
    #         widget.close()

    #     return super().close()

    def remove_all_but_main(self):
        for widget in (self.tab_2, self.tab_3, self.tab_4):
            # Close the widget
            widget.close()

            self.tabWidget.removeTab(self.tabWidget.indexOf(widget))

    def create_tabs(self):
        self.tab_2 = widget_mdb.Ui_widget_mdb(base_widget=self)
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.tabWidget.addTab(self.tab_4, "")
        self.retranslateUi(self)


    def refresh_widgets(self, func):
        if not self.ask_widgets_close():
            return
        
        self.app.setOverrideCursor(QCursor(Qt.WaitCursor))
        func()
        self.app.restoreOverrideCursor()

        self.remove_all_but_main()
        self.create_tabs()

    def ask_widgets_close(self):
        for i in range(self.tabWidget.count()):
            widget = self.tabWidget.widget(i)
            # Check if it has ask_close() method
            if hasattr(widget, "ask_close"):
                # If it does, call it
                if not widget.ask_close():
                    return False
        
        return True


    def closeEvent(self, a0: QCloseEvent) -> None:
        print("closeEvent")

        if not self.ask_widgets_close():
            a0.ignore()
            return

        return super().closeEvent(a0)

    def setupUi(self, widget_tabs):
        if not widget_tabs.objectName():
            widget_tabs.setObjectName(u"widget_tabs")
        widget_tabs.resize(678, 459)
        
        # Disable resizing
        widget_tabs.setFixedSize(widget_tabs.size())

        widget_tabs.setWindowTitle(u"Carotene")
        self.verticalLayout = QVBoxLayout(widget_tabs)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(widget_tabs)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tab_home = widget_main.Ui_widget_main(base_widget=self)
        self.tab_home.setObjectName(u"tab_home")
        self.tabWidget.addTab(self.tab_home, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_home), u"Home")

        self.verticalLayout.addWidget(self.tabWidget)

        self.create_tabs()


        self.retranslateUi(widget_tabs)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(widget_tabs)
    # setupUi

    def retranslateUi(self, widget_tabs):
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("widget_tabs", u"MDB", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("widget_tabs", u"Assembly", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("widget_tabs", u"Story", None))
        pass
    # retranslateUi

