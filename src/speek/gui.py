import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QScrollArea, QLabel, QFrame, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QVariantAnimation
from PyQt6.QtGui import QColor

class BackendSignals(QObject):
    """Secure bridge between the background AI and the Main GUI Thread"""
    new_transcription = pyqtSignal(str)
    show_window = pyqtSignal()
    hide_window = pyqtSignal()

class TranscriptionBubble(QWidget):
    def __init__(self, text: str):
        super().__init__()
        
        self.frame = QFrame(self)
        self.base_style = "border: 1px solid #444; border-radius: 4px;"
        self.frame.setStyleSheet(f"background-color: #005f87; {self.base_style}")
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label.setStyleSheet("border: none; padding: 6px; padding-bottom: 25px; background: transparent;") 
        frame_layout.addWidget(self.label)
        
        self.btn_copy = QPushButton("Copy", self.frame)
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.setFixedWidth(50)
        self.btn_copy.setFixedHeight(20)
        self.default_btn_style = "background-color: #555; color: #fff; border: none; border-radius: 4px; padding: 2px; font-size: 10px;"
        self.btn_copy.setStyleSheet(self.default_btn_style)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.addWidget(self.frame)

        # THE FADE ANIMATION
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(2000) # 2-second fade
        self.anim.setStartValue(QColor("#005f87")) # Bright Highlight Blue
        self.anim.setEndValue(QColor("#2d2d2d"))   # Default Dark Gray
        self.anim.valueChanged.connect(self.update_bg_color)
        self.anim.start()

    def update_bg_color(self, color):
        self.frame.setStyleSheet(f"background-color: {color.name()}; {self.base_style}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn_x = self.frame.width() - self.btn_copy.width() - 5
        btn_y = self.frame.height() - self.btn_copy.height() - 5
        self.btn_copy.move(btn_x, btn_y)
        self.btn_copy.raise_()

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.label.text())
        self.btn_copy.setText("Copied!")
        self.btn_copy.setStyleSheet("background-color: #2ea043; color: #ffffff; border: none; border-radius: 4px; padding: 2px; font-size: 10px;")
        QTimer.singleShot(1500, self.reset_copy_button)

    def reset_copy_button(self):
        self.btn_copy.setText("Copy")
        self.btn_copy.setStyleSheet(self.default_btn_style)

class SpeekWindow(QWidget):
    def __init__(self, signals: BackendSignals):
        super().__init__()
        self.signals = signals
        self.signals.new_transcription.connect(self.append_bubble)
        self.signals.show_window.connect(self.show)
        self.signals.hide_window.connect(self.recording_stopped)
        
        # Thread-Safe Python Booleans for background threads to read safely!
        self.is_mic_enabled = False # False = Desktop, True = Mic
        self.is_translate_enabled = False
        self.is_machine_gun_enabled = False
        
        self.current_opacity = 1.0
        self.current_font_size = 13
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Speek Terminal")
        self.resize(500, 400)
        
        self.update_stylesheet()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: #1e1e1e;")
        
        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.scroll_container)
        main_layout.addWidget(self.scroll_area, stretch=4)
        
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.rangeChanged.connect(lambda min_val, max_val: scrollbar.setValue(max_val))
        
        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(4, 0, 0, 0)
        
        self.btn_pin = QPushButton("📌 Pin")
        self.btn_pin.setCheckable(True)
        control_layout.addWidget(self.btn_pin)

        # Dynamic Audio Source Toggle Button
        self.btn_source = QPushButton("🎧 Desktop")
        self.btn_source.setCheckable(True)
        self.btn_source.setChecked(False) # Default to Desktop
        self.btn_source.setToolTip("Toggle between Desktop Audio and Microphone")
        self.btn_source.toggled.connect(self.on_source_toggled)
        control_layout.addWidget(self.btn_source)

        self.btn_machine_gun = QPushButton("🔫 Type")
        self.btn_machine_gun.setCheckable(True)
        self.btn_machine_gun.toggled.connect(lambda c: setattr(self, 'is_machine_gun_enabled', c))
        control_layout.addWidget(self.btn_machine_gun)
        
        self.btn_translate = QPushButton("🌐 EN")
        self.btn_translate.setCheckable(True)
        self.btn_translate.toggled.connect(lambda c: setattr(self, 'is_translate_enabled', c))
        control_layout.addWidget(self.btn_translate)

        self.btn_copy_all = QPushButton("Copy All")
        self.btn_copy_all.clicked.connect(self.copy_all)
        control_layout.addWidget(self.btn_copy_all)
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_all)
        control_layout.addWidget(self.btn_clear)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout, stretch=1)

    def on_source_toggled(self, checked):
        """Dynamically switches the button text and sets the thread-safe state"""
        self.is_mic_enabled = checked
        if checked:
            self.btn_source.setText("🎙️ Mic")
        else:
            self.btn_source.setText("🎧 Desktop")

    def update_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: {self.current_font_size}px; }}
            QPushButton {{ background-color: #333333; border: 1px solid #555555; border-radius: 4px; padding: 6px; margin-bottom: 4px; transition: 0.1s;}}
            QPushButton:hover {{ background-color: #444444; }}
            QPushButton:pressed {{ background-color: #555555; border: 1px solid #888888; }}
            QPushButton:checked {{ background-color: #005f87; border: 1px solid #00afff; }}
        """)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2d2d2d; color: #fff; border: 1px solid #555; } QMenu::item:selected { background-color: #444; }")
        
        opacity_menu = menu.addMenu("Opacity")
        act_op_inc = opacity_menu.addAction("Increase (+10%)")
        act_op_dec = opacity_menu.addAction("Decrease (-10%)")
        act_op_inc.triggered.connect(lambda: self.change_opacity(0.1))
        act_op_dec.triggered.connect(lambda: self.change_opacity(-0.1))
        
        font_menu = menu.addMenu("Font Size")
        act_font_inc = font_menu.addAction("Increase (+1)")
        act_font_dec = font_menu.addAction("Decrease (-1)")
        act_font_inc.triggered.connect(lambda: self.change_font(1))
        act_font_dec.triggered.connect(lambda: self.change_font(-1))
        
        menu.exec(event.globalPos())

    def change_opacity(self, delta: float):
        self.current_opacity = max(0.2, min(1.0, self.current_opacity + delta))
        self.setWindowOpacity(self.current_opacity)

    def change_font(self, delta: int):
        self.current_font_size = max(8, min(30, self.current_font_size + delta))
        self.update_stylesheet()

    def append_bubble(self, text: str):
        if text:
            bubble = TranscriptionBubble(text)
            self.scroll_layout.addWidget(bubble)
            # Auto-scroll is now perfectly handled by the rangeChanged signal in init_ui!

    def copy_all(self):
        all_texts = []
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if isinstance(widget, TranscriptionBubble):
                all_texts.append(widget.label.text())
        QApplication.clipboard().setText("\\n\\n".join(all_texts))
        
        self.btn_copy_all.setText("Copied!")
        self.btn_copy_all.setStyleSheet("background-color: #2ea043; color: white; border: 1px solid #2ea043;")
        QTimer.singleShot(1500, lambda: (
            self.btn_copy_all.setText("Copy All"),
            self.btn_copy_all.setStyleSheet("")
        ))

    def clear_all(self):
        for i in reversed(range(self.scroll_layout.count())): 
            self.scroll_layout.itemAt(i).widget().setParent(None)
            
    def recording_stopped(self):
        if not self.btn_pin.isChecked():
            self.hide()

    def closeEvent(self, event):
        """Intercept the 'X' close button so it hides instead of destroying the window"""
        event.ignore()
        self.hide()