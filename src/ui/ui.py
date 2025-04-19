from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QComboBox,
    QPushButton, QTextEdit, QLineEdit, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat App")
        self.setGeometry(0, 0, 852, 508)

        central_widget = QWidget(self)
        central_layout = QHBoxLayout(central_widget)

        dm_frame = QFrame(self)
        dm_frame.setFrameShape(QFrame.Box)
        dm_frame.setFrameShadow(QFrame.Raised)
        dm_layout = QVBoxLayout(dm_frame)

        chat_with_label = QLabel("Chat With:", self)
        font = QFont()
        font.setPointSize(10)
        chat_with_label.setFont(font)
        dm_layout.addWidget(chat_with_label)

        self.user_dropdown = QComboBox(self)
        dm_layout.addWidget(self.user_dropdown)

        self.open_dm_button = QPushButton("Open DM", self)
        dm_layout.addWidget(self.open_dm_button)

        server_frame = QFrame(self)
        server_frame.setFrameShape(QFrame.Box)
        server_frame.setFrameShadow(QFrame.Raised)
        server_layout = QVBoxLayout(server_frame)

        server_label = QLabel("Server:", self)
        server_label.setFont(font)
        server_layout.addWidget(server_label)

        self.server_label = QLabel()
        server_layout.addWidget(self.server_label)
        self.server_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.server_label.setStyleSheet("""
            QLabel {
                border: 1px solid gray;
                border-radius: 5px;
                padding: 2px 2px;
                background-color: white;
                min-height: 22px;
            }
        """)

        self.change_server_button = QPushButton("Change Server", self)
        server_layout.addWidget(self.change_server_button)

        debug_frame = QFrame(self)
        debug_frame.setFrameShape(QFrame.Box)
        debug_frame.setFrameShadow(QFrame.Raised)
        debug_layout = QVBoxLayout(debug_frame)

        self.text_edit = QTextEdit(self)
        debug_layout.addWidget(self.text_edit)

        main_frame = QFrame(self)
        main_frame.setFrameShape(QFrame.Box)
        main_frame.setFrameShadow(QFrame.Raised)
        main_layout = QVBoxLayout(main_frame)

        self.chat_box = QTextEdit(self)
        self.chat_box.setReadOnly(True)
        self.chat_box.setMinimumHeight(420)
        main_layout.addWidget(self.chat_box)

        self.message_entry = QLineEdit(self)
        self.message_entry.setMinimumHeight(30)
        main_layout.addWidget(self.message_entry)

        self.send_button = QPushButton("Send", self)
        main_layout.addWidget(self.send_button)

        self.typing_status = QLineEdit(self)
        self.typing_status.setText("Typing: ")
        self.typing_status.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: gray;
            }
        """)
        self.typing_status.setReadOnly(True)
        main_layout.addWidget(self.typing_status)

        side_layout = QVBoxLayout()
        side_layout.addWidget(dm_frame)
        side_layout.addWidget(server_frame)
        side_layout.addWidget(debug_frame)
        central_layout.addLayout(side_layout, stretch=1)
        central_layout.addWidget(main_frame, stretch=3)

        self.setCentralWidget(central_widget)
