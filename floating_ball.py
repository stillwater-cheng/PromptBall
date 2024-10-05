import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QToolTip,
                             QDialog, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QCursor, QIcon, QFontMetrics
import os
import json
import unicodedata

def set_startup():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, "FloatingBallApp", 0, winreg.REG_SZ,
                          sys.executable)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"设置开机自启动失败：{e}")

# 定义样式表
STYLE_SHEET = """
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 8px;
    padding: 5px;
}

QListWidget::item {
    color: #333333;
    padding: 4px 8px;
    margin: 1px 0;
    border-radius: 5px;
    height: 30px;  /* 固定每个选项的高度 */
}

QListWidget::item:hover {
    background-color: #f0f0f0;
}

QListWidget::item:selected {
    background-color: #e6f7ff;
    color: #1890ff;
}
"""

class OptionsListWidget(QListWidget):
    def __init__(self, options, parent_window):
        super().__init__()
        self.options = options
        self.parent_window = parent_window

        # 设置为每像素滚动模式
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        # 调整滚动速度
        self.verticalScrollBar().setSingleStep(10)

        # 固定选项的高度
        self.setUniformItemSizes(True)  # 启用统一的项大小

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            if event.button() == Qt.LeftButton:
                # 左键点击，复制到剪切板
                index = self.row(item)
                text = self.options[index]
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                self.parent_window.bounce_animation()
                self.parent().close()
            elif event.button() == Qt.RightButton:
                # 右键点击，删除选项
                index = self.row(item)
                del self.options[index]
                self.parent_window.option_set.discard(item.toolTip())
                self.parent_window.save_options()
                self.takeItem(index)
                self.parent_window.bounce_animation()
        else:
            super().mousePressEvent(event)

class OptionsDialog(QDialog):
    def __init__(self, options, parent_window):
        super().__init__(parent_window)
        self.options = options
        self.parent_window = parent_window
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        # 使用自定义的 OptionsListWidget
        self.list_widget = OptionsListWidget(self.options, self.parent_window)

        # 计算20个中文字的宽度
        font_metrics = self.list_widget.fontMetrics()
        sample_text = '中' * 20  # 20个中文字
        text_width = font_metrics.boundingRect(sample_text).width()

        # 设置固定宽度，并加上一些边距
        self.list_widget.setFixedWidth(text_width + 40)  # 加上边距

        # 设置文本省略模式
        self.list_widget.setTextElideMode(Qt.ElideRight)

        # 隐藏垂直滚动条，但保留滚动功能
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.verticalScrollBar().setVisible(False)

        # 禁用水平滚动条
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for option in self.options:
            display_text = option[:20]  # 仅显示前20个中文字
            if len(option) > 20:
                display_text += '...'  # 超出部分显示省略号
            # 使用图标
            icon = QIcon.fromTheme("edit-copy")
            item = QListWidgetItem(icon, display_text)
            item.setToolTip(option)  # 完整内容作为提示

            # 设置固定高度
            item.setSizeHint(QSize(text_width + 40, 30))  # 固定高度为30

            self.list_widget.addItem(item)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 设置窗口透明度
        self.setWindowOpacity(0.9)

        # 应用样式表
        self.setStyleSheet(STYLE_SHEET)

class FloatingBall(QWidget):
    def __init__(self):
        super().__init__()

        # 检查并设置自启动
        if os.name == 'nt':
            set_startup()

        # 初始化变量
        self.is_moving = False
        self.is_pressing = False
        self.press_pos = QPoint()
        self.options = []
        self.option_set = set()
        self.default_save_dir = os.path.join(os.path.expanduser("~"), ".floating_ball")
        self.config_file_path = os.path.join(self.default_save_dir, "config.json")
        self.current_emoji = '💎'  # 默认表情符号

        # 加载配置和选项
        self.load_config()
        self.load_options()

        # 设置窗口属性
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置主标签（悬浮球）
        self.label = QLabel(self.current_emoji, self)
        self.label.setStyleSheet("font-size: 36px;")
        self.label.setAlignment(Qt.AlignCenter)

        # 绑定事件
        self.label.mousePressEvent = self.mouse_press_event
        self.label.mouseReleaseEvent = self.mouse_release_event
        self.label.mouseMoveEvent = self.mouse_move_event

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 显示窗口
        self.resize(50, 50)
        self.show()

    # 事件处理
    def mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ControlModifier:
                # Ctrl键被按下，退出程序
                QApplication.quit()
            else:
                self.is_moving = False
                self.press_pos = event.globalPos() - self.pos()
                self.is_pressing = True
        elif event.button() == Qt.RightButton:
            modifiers = event.modifiers()
            if modifiers & Qt.ControlModifier:
                # Ctrl + 右键，设置新的保存路径
                self.set_new_save_path()
            elif modifiers & Qt.ShiftModifier:
                # Shift + 右键，设置新的表情符号
                self.set_new_emoji()
            else:
                self.add_option_from_clipboard()

    def mouse_move_event(self, event):
        if event.buttons() == Qt.LeftButton and self.is_pressing:
            move_pos = event.globalPos() - self.press_pos
            self.move(move_pos)
            self.is_moving = True

    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton:
            if not self.is_moving:
                self.show_menu()
            self.is_moving = False
            self.is_pressing = False

    # 新增方法：设置新的表情符号
    def set_new_emoji(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if self.is_emoji(text):
            self.current_emoji = text  # 更新当前表情符号
            self.label.setText(text)
            self.save_config()
            self.bounce_animation()
        else:
            QToolTip.showText(QCursor.pos(), "剪切板中的内容不是表情符号。", self)

    # 新增方法：判断是否为表情符号
    def is_emoji(self, text):
        if len(text) != 1:
            return False
        char = text
        try:
            return unicodedata.category(char) in ['So', 'Sk', 'Cs']
        except TypeError:
            return False

    # 显示选项列表
    def show_menu(self):
        self.options_dialog = OptionsDialog(self.options, self)
        self.options_dialog.move(QCursor.pos())
        self.options_dialog.exec_()

    # 添加选项
    def add_option_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            if text in self.option_set:
                # 已存在，不添加
                QToolTip.showText(QCursor.pos(), "该文本已存在。", self)
            else:
                self.options.append(text)
                self.option_set.add(text)
                self.save_options()
                self.bounce_animation()
        else:
            QToolTip.showText(QCursor.pos(), "剪切板中没有文本。", self)

    # 设置新的保存路径
    def set_new_save_path(self):
        clipboard = QApplication.clipboard()
        path = clipboard.text()
        if os.path.isdir(path):
            self.save_dir = path
            self.options_file = os.path.join(self.save_dir, "options.json")
            self.save_options()
            self.save_config()
            self.bounce_animation()
        else:
            QToolTip.showText(QCursor.pos(), "剪切板中的路径无效。", self)

    # 保存配置
    def save_config(self):
        config = {
            'save_dir': self.save_dir,
            'emoji': self.current_emoji  # 保存当前表情符号
        }
        if not os.path.exists(self.default_save_dir):
            os.makedirs(self.default_save_dir)
        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    # 加载配置
    def load_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.save_dir = config.get('save_dir', self.default_save_dir)
            self.current_emoji = config.get('emoji', '💎')
        else:
            self.save_dir = self.default_save_dir
            self.current_emoji = '💎'

        # 更新 options.json 的路径
        self.options_file = os.path.join(self.save_dir, "options.json")

    # 保存选项
    def save_options(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        with open(self.options_file, 'w', encoding='utf-8') as f:
            json.dump(self.options, f, ensure_ascii=False, indent=4)

    # 加载选项
    def load_options(self):
        if os.path.exists(self.options_file):
            with open(self.options_file, 'r', encoding='utf-8') as f:
                self.options = json.load(f)
            self.option_set = set(self.options)

    # 悬浮球跳动动画
    def bounce_animation(self):
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(500)
        start_pos = self.pos()
        end_pos = QPoint(start_pos.x(), start_pos.y() - 20)
        self.animation.setStartValue(start_pos)
        self.animation.setKeyValueAt(0.5, end_pos)
        self.animation.setEndValue(start_pos)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)
        self.animation.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    floating_ball = FloatingBall()
    sys.exit(app.exec_())
