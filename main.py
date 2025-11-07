# main.py
from PySide6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout,
    QWidget, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QMenuBar,
    QMenu, QToolBar, QDialog, QLabel, QCheckBox, QDialogButtonBox, QStatusBar,
    QFontComboBox, QSpinBox, QComboBox, QColorDialog, QFontDialog, QSystemTrayIcon)
from PySide6.QtGui import QPalette, QColor, QAction, QIcon, QFont, QTextCharFormat, QActionGroup
from PySide6.QtCore import Qt, QTimer
import os, sys
from datetime import datetime
from core.theme_manager import ThemeManager, Theme
from core.voice_manager import VoiceManager
from core.splash_screen import SplashScreen


# === Helper function: Apply dark theme ===
def apply_dark_theme(app):
    palette = QPalette()

    # Backward-compatible attribute usage
    def set_color(role_name, color):
        role = getattr(QPalette, role_name, None)
        if role is not None:
            palette.setColor(role, color)

    set_color("Window", QColor(30, 30, 30))
    set_color("WindowText", Qt.white)
    set_color("Base", QColor(45, 45, 45))
    set_color("Text", Qt.white)
    set_color("Button", QColor(60, 60, 60))
    set_color("ButtonText", Qt.white)
    set_color("Highlight", QColor(200, 0, 0))
    set_color("HighlightedText", Qt.black)

    app.setPalette(palette)


# === Main window ===
class TermsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terms & Conditions")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Title with custom font
        title = QLabel("DurangDBack Terms of Use")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Terms text
        terms_text = QTextEdit()
        terms_text.setReadOnly(True)
        terms_text.setHtml("""
            <h3>Welcome to DurangDBack</h3>
            <p>By using this application, you agree to the following terms:</p>
            <ul>
                <li>Your notes are stored locally on your device</li>
                <li>Regular backups are automatically created</li>
                <li>You are responsible for managing your saved notes</li>
                <li>This software is provided "as is" without warranty</li>
            </ul>
            <p><b>Privacy:</b> We respect your privacy. No data is collected or transmitted.</p>
            <p><b>Backups:</b> Notes are backed up in the 'backup' folder automatically.</p>
        """)
        layout.addWidget(terms_text)

        # Checkbox for acceptance
        self.accept_checkbox = QCheckBox("I accept the terms and conditions")
        layout.addWidget(self.accept_checkbox)

        # Standard buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        if not self.accept_checkbox.isChecked():
            QMessageBox.warning(self, "Terms & Conditions",
                              "You must accept the terms to continue.")
            return
        super().accept()


class DurangMain(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Show splash screen``
        self.splash = SplashScreen()
        self.splash.show()
        
        # Initialize voice manager
        self.voice_manager = VoiceManager()
        self.voice_manager.voice_command_received.connect(self.handle_voice_command)
        
        # Use timer to simulate loading and initialize UI after splash
        QTimer.singleShot(2000, self.delayed_init)
        
        # Initialize paths
        self.notes_dir = os.path.join(os.getcwd(), "notes")
        self.backup_dir = os.path.join(os.getcwd(), "backup")
        os.makedirs(self.notes_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def delayed_init(self):
        self.setWindowTitle("DurangDBack - Notepad")
        self.setMinimumSize(600, 400)
        
        # Setup UI components
        self.setup_menubar()
        self.setup_toolbar()
        self.setup_central_widget()
        self.setup_statusbar()
        
        # Show terms on first run
        self.check_first_run()
        
        # Close splash and show main window
        self.splash.close()
        self.show()
        
        # Start voice recognition in background
        self.voice_manager.start_listening()
        
    def handle_voice_command(self, command):
        """Handle voice commands received from VoiceManager"""
        command = command.lower()
        if "save" in command:
            self.save_note()
        elif "new" in command:
            self.new_note()
        elif "list" in command:
            self.list_notes()
        elif "bold" in command:
            self.toggle_bold()
        elif "italic" in command:
            self.toggle_italic()
        
        # Show feedback in status bar
        self.statusBar().showMessage(f"Voice command: {command}", 3000)
    
    def setup_menubar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_note)
        file_menu.addAction(new_action)
        
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_note)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Format submenu
        format_menu = edit_menu.addMenu("&Format")
        
        self.bold_action = QAction("&Bold", self)
        self.bold_action.setShortcut("Ctrl+B")
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self.toggle_bold)
        format_menu.addAction(self.bold_action)
        
        self.italic_action = QAction("&Italic", self)
        self.italic_action.setShortcut("Ctrl+I")
        self.italic_action.setCheckable(True)
        self.italic_action.triggered.connect(self.toggle_italic)
        format_menu.addAction(self.italic_action)
        
        format_menu.addSeparator()
        
        # Font submenu
        font_menu = format_menu.addMenu("&Font")
        self.setup_font_actions(font_menu)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")
        self.setup_theme_actions(theme_menu)
        
        # Word wrap
        wrap_action = QAction("&Word Wrap", self)
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)
        wrap_action.triggered.connect(lambda checked: self.text_edit.setLineWrapMode(
            QTextEdit.WidgetWidth if checked else QTextEdit.NoWrap))
        view_menu.addAction(wrap_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        terms_action = QAction("&Terms && Conditions", self)
        terms_action.triggered.connect(self.show_terms)
        help_menu.addAction(terms_action)
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_theme_actions(self, theme_menu):
        self.theme_group = QActionGroup(self)
        
        for theme in Theme:
            action = QAction(theme.value, self)
            action.setCheckable(True)
            action.setData(theme)
            if theme == Theme.DARK_RED:  # Default theme
                action.setChecked(True)
            action.triggered.connect(self.change_theme)
            self.theme_group.addAction(action)
            theme_menu.addAction(action)
            
    def setup_font_actions(self, font_menu):
        # Font family
        font_family_action = QAction("Font &Family...", self)
        font_family_action.triggered.connect(self.choose_font_family)
        font_menu.addAction(font_family_action)
        
        # Font size
        font_size_menu = font_menu.addMenu("Font &Size")
        sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
        for size in sizes:
            action = QAction(str(size), self)
            action.triggered.connect(lambda checked, s=size: self.set_font_size(s))
            font_size_menu.addAction(action)
        
        # Font color
        font_color_action = QAction("Font &Color...", self)
        font_color_action.triggered.connect(self.choose_font_color)
        font_menu.addAction(font_color_action)
    
    def setup_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # New note button
        new_btn = QPushButton("New")
        new_btn.setStatusTip("Create a new note")
        new_btn.clicked.connect(self.new_note)
        toolbar.addWidget(new_btn)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setStatusTip("Save current note")
        save_btn.clicked.connect(self.save_note)
        toolbar.addWidget(save_btn)
        
        # List notes button
        list_btn = QPushButton("List Notes")
        list_btn.setStatusTip("Show saved notes")
        list_btn.clicked.connect(self.list_notes)
        toolbar.addWidget(list_btn)
    
    def setup_central_widget(self):
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Start typing your note...")
        
        # Set a nicer font for the editor
        font = QFont("Segoe UI", 11)
        self.text_edit.setFont(font)
        
        # Track text formatting
        self.text_edit.currentCharFormatChanged.connect(self.format_changed)
        
        # Enable rich text features
        self.text_edit.setAcceptRichText(True)
        
        # Add format toolbar
        format_toolbar = QToolBar("Format")
        self.addToolBar(Qt.TopToolBarArea, format_toolbar)
        
        # Font combo
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(
            lambda font: self.text_edit.setFontFamily(font.family()))
        format_toolbar.addWidget(self.font_combo)
        
        # Font size combo
        self.size_combo = QComboBox()
        self.size_combo.addItems([str(s) for s in [8,9,10,11,12,14,16,18,20,22,24,28,36]])
        self.size_combo.setCurrentText("11")
        self.size_combo.currentTextChanged.connect(
            lambda size: self.text_edit.setFontPointSize(float(size)))
        format_toolbar.addWidget(self.size_combo)
        
        # Bold, italic buttons
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.clicked.connect(self.toggle_bold)
        format_toolbar.addWidget(self.bold_btn)
        
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.clicked.connect(self.toggle_italic)
        format_toolbar.addWidget(self.italic_btn)
        
        # Color button
        color_btn = QPushButton("Color")
        color_btn.clicked.connect(self.choose_font_color)
        format_toolbar.addWidget(color_btn)
        
        # Central widget setup
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.text_edit)
        self.setCentralWidget(central_widget)
        
    def format_changed(self, format):
        """Update formatting buttons when text format changes"""
        self.bold_btn.setChecked(format.font().bold())
        self.italic_btn.setChecked(format.font().italic())
        
        # Update font combos
        font_family = format.font().family()
        if self.font_combo.currentFont().family() != font_family:
            self.font_combo.setCurrentText(font_family)
            
        size = str(int(format.font().pointSize()))
        if self.size_combo.currentText() != size:
            self.size_combo.setCurrentText(size)
            
    def toggle_bold(self):
        """Toggle bold formatting on selected text"""
        if self.text_edit.hasFocus():
            self.text_edit.setFontWeight(
                QFont.Bold if not self.text_edit.fontWeight() == QFont.Bold
                else QFont.Normal)
        
    def toggle_italic(self):
        """Toggle italic formatting on selected text"""
        self.text_edit.setFontItalic(not self.text_edit.fontItalic())
        
    def choose_font_family(self):
        """Open font selection dialog"""
        font, ok = QFontDialog.getFont(self.text_edit.currentFont(), self)
        if ok:
            self.text_edit.setCurrentFont(font)
            
    def set_font_size(self, size):
        """Set font size for selected text"""
        self.text_edit.setFontPointSize(float(size))
        
    def choose_font_color(self):
        """Open color picker for text color"""
        color = QColorDialog.getColor(self.text_edit.textColor(), self)
        if color.isValid():
            self.text_edit.setTextColor(color)
            
    def change_theme(self):
        """Change application theme"""
        action = self.sender()
        if action and action.data():
            theme = action.data()
            ThemeManager.apply_theme(QApplication.instance(), theme)
            app = QApplication.instance()
            app.setStyleSheet(ThemeManager.get_theme_stylesheet(theme))
    
    def setup_statusbar(self):
        self.statusBar().showMessage("Ready")
    
    def check_first_run(self):
        if not os.path.exists(os.path.join(self.notes_dir, ".accepted_terms")):
            if self.show_terms() == QDialog.Accepted:
                with open(os.path.join(self.notes_dir, ".accepted_terms"), "w") as f:
                    f.write(datetime.now().isoformat())
    
    def show_terms(self):
        dialog = TermsDialog(self)
        return dialog.exec()
    
    def show_about(self):
        QMessageBox.about(self, "About DurangDBack",
                         """<h3>DurangDBack Notepad</h3>
                         <p>A professional note-taking application with automatic backups.</p>
                         <p><b>Version:</b> 1.0.0</p>
                         <p><b>Created by:</b> QRTQuick</p>""")

    def confirm_action(self, title, message):
        return QMessageBox.question(self, title, message,
                                  QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes

    def new_note(self):
        if self.text_edit.toPlainText().strip():
            if not self.confirm_action("New Note",
                                     "Do you want to clear the current note?"):
                return
        self.text_edit.clear()
        self.statusBar().showMessage("Created new note")

    def save_note(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Empty Note", "You can't save an empty note!")
            return
        
        # Generate default filename with timestamp
        default_name = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Note", 
            os.path.join(self.notes_dir, default_name),
            "Text Files (*.txt)")

        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            
            # Create backup
            backup_path = os.path.join(self.backup_dir, os.path.basename(path))
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            QMessageBox.information(self, "Saved", f"Note saved at:\n{path}")
            self.statusBar().showMessage(f"Saved note: {os.path.basename(path)}")

    def list_notes(self):
        notes = os.listdir(self.notes_dir)
        notes = [n for n in notes if n.endswith('.txt')]
        if not notes:
            QMessageBox.information(self, "No Notes", "No saved notes found.")
            return

        # Create a more detailed notes list
        note_info = []
        for note in notes:
            path = os.path.join(self.notes_dir, note)
            size = os.path.getsize(path)
            modified = datetime.fromtimestamp(os.path.getmtime(path))
            note_info.append(f"{note}\nSize: {size/1024:.1f}KB\nModified: {modified:%Y-%m-%d %H:%M}")
        
        QMessageBox.information(self, "Saved Notes", "\n\n".join(note_info))
        self.statusBar().showMessage(f"Found {len(notes)} notes")


# === Run App ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    
    # Create system tray icon for voice feedback
    tray_icon = QSystemTrayIcon(QIcon(os.path.join(os.getcwd(), "assets", "app_icon.png")), app)
    tray_icon.setToolTip("DurangDBack - Voice Commands Active")
    tray_icon.show()
    
    window = DurangMain()
    
    # Handle application shutdown
    def cleanup():
        if hasattr(window, 'voice_manager'):
            window.voice_manager.stop_listening()
        tray_icon.hide()
    
    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec())