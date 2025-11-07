import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QMessageBox, QFileDialog
)
from PySide6.QtGui import QAction


class DurangWindow(QMainWindow):
    def __init__(self, note_manager):
        super().__init__()
        self.note_manager = note_manager
        self.setWindowTitle("DurangDBack - Simple Notepad")
        self.resize(800, 600)

        self.current_file = None

        # Setup UI
        self._build_ui()
        self._build_menu()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type your notes here...")
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        self.new_btn = QPushButton("New")
        self.save_btn = QPushButton("Save")
        self.list_btn = QPushButton("List Notes")

        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.list_btn)

        self.new_btn.clicked.connect(self.new_note)
        self.save_btn.clicked.connect(self.save_note)
        self.list_btn.clicked.connect(self.list_notes)

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_note)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_note)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.list_notes)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        for act in [new_action, save_action, open_action, exit_action]:
            file_menu.addAction(act)

    def new_note(self):
        self.text_edit.clear()
        self.current_file = None
        self.setWindowTitle("DurangDBack - New Note")

    def save_note(self):
        content = self.text_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Empty Note", "Please type something before saving.")
            return

        if not self.current_file:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Note", self.note_manager.notes_path, "Text Files (*.txt)"
            )
            if not filename:
                return
            filename = os.path.basename(filename)
        else:
            filename = self.current_file

        self.note_manager.save_note(filename, content)
        self.current_file = filename

        QMessageBox.information(self, "Saved", f"Note '{filename}' saved successfully!")
        self.setWindowTitle(f"DurangDBack - {filename}")

    def list_notes(self):
        files = self.note_manager.list_notes()
        if not files:
            QMessageBox.information(self, "No Notes", "No saved notes yet.")
            return

        dialog = QFileDialog(self, "Open Note")
        dialog.setDirectory(self.note_manager.notes_path)
        dialog.setNameFilter("Text Files (*.txt)")
        dialog.setFileMode(QFileDialog.ExistingFile)

        if dialog.exec():
            path = dialog.selectedFiles()[0]
            filename = os.path.basename(path)
            content = self.note_manager.load_note(filename)
            self.text_edit.setText(content)
            self.current_file = filename
            self.setWindowTitle(f"DurangDBack - {filename}")