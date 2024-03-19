from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import *
import time

def str_to_char_data(text: str) -> list:
    in_tag = False
    tag_active = False

    text_chars = []

    cur_tags = []
    cur_tag = ""

    for char in text:
        is_bold = False
        is_italic = False

        if char == "<":
            in_tag = True
            tag_active = True
            cur_tag = ""
            continue

        if in_tag and char == "/":
            tag_active = False
            continue

        if in_tag and char == ">":
            in_tag = False

            if not tag_active:
                cur_tags.pop()
            else:
                cur_tags.append(cur_tag)
            continue

        if in_tag:
            cur_tag += char
            continue

        if "b" in cur_tags:
            is_bold = True

        if "i" in cur_tags:
            is_italic = True

        text_chars.append((char, is_bold, is_italic))
    
    return text_chars

def char_data_to_str(char_data: list) -> str:
    # Reconstruct the text
    new_text = ""
    prev_bold = False
    prev_italic = False

    tag_stack = []

    for char, is_bold, is_italic in char_data:
        if prev_bold and prev_italic:
            if prev_bold != is_bold or prev_italic != is_italic:
                for i in range(len(tag_stack)):
                    new_text += tag_stack.pop()
                prev_bold = False
                prev_italic = False
        
        if prev_bold != is_bold:
            if is_bold:
                new_text += "<b>"
                tag_stack.append("</b>")
            else:
                new_text += tag_stack.pop()
        if prev_italic != is_italic:
            if is_italic:
                new_text += "<i>"
                tag_stack.append("</i>")
            else:
                new_text += tag_stack.pop()
        
        new_text += char

        prev_bold = is_bold
        prev_italic = is_italic
    
    if prev_bold:
        new_text += "</b>"
    if prev_italic:
        new_text += "</i>"
    
    return new_text

def _make_bold(char_format):
    pen = QPen()
    pen.setColor(QColor("#000"))
    pen.setWidth(1)
    char_format.setTextOutline(pen)
    char_format.setFontWeight(QFont.Bold)
    return char_format


def set_text(text: str, widget: QPlainTextEdit):
    cursor = widget.textCursor()
    widget.clear()

    text = text.replace("\r\n", "\n").replace(" \n", "\n")
    char_data = str_to_char_data(text)

    cursor.setPosition(0)
    widget.setTextCursor(cursor)

    for char, is_bold, is_italic in char_data:
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Normal)

        if is_bold:
            _make_bold(char_format)

        char_format.setFontItalic(is_italic)
        widget.setCurrentCharFormat(char_format)
        widget.textCursor().insertText(char)


def get_text(widget: QPlainTextEdit) -> str:
    text = widget.toPlainText()
    cursor = widget.textCursor()

    char_data = []

    for i, char in enumerate(text):
        cursor.setPosition(i+1)
        fmt = cursor.charFormat()
        is_bold = fmt.fontWeight() == QFont.Bold
        is_italic = fmt.fontItalic()

        char_data.append((char, is_bold, is_italic))
    
    text = char_data_to_str(char_data)
    text = text.replace(" \n", "\n").replace("\n", " \n")
    return text

class UmaPlainTextEdit(QPlainTextEdit):
    click_count = 0
    last_click = 0
    click_cooldown = 0.3

    def _check_for_triple_click(self, e: QMouseEvent) -> None:
        # Triple click = select all.

        is_left_click = e.button() == Qt.LeftButton

        if not is_left_click:
            return
        
        cur_time = time.time()
        dtime = cur_time - self.last_click
        if dtime < self.click_cooldown:
            self.click_count += 1
        else:
            self.click_count = 1
        
        self.last_click = cur_time

        if self.click_count == 3:
            cursor = self.textCursor()

            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()

                text = self.toPlainText()

                left_newline = text.rfind("\n", 0, start)
                right_newline = text.find("\n", end)

                if left_newline == -1:
                    left_newline = 0
                else:
                    left_newline += 1

                if right_newline == -1:
                    right_newline = len(text)

                cursor.setPosition(left_newline)
                cursor.setPosition(right_newline, QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)
                return True
            self.click_count = 4

        if self.click_count >= 4:
            self.selectAll()
            return True
        return False


    def mousePressEvent(self, e: QMouseEvent) -> None:
        if self._check_for_triple_click(e):
            return

        return super().mousePressEvent(e)
    
    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        if self._check_for_triple_click(e):
            return

        return super().mouseDoubleClickEvent(e)