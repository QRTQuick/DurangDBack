# main.py
from PySide6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout,
    QWidget, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QMenuBar,
    QMenu, QToolBar, QDialog, QLabel, QCheckBox, QDialogButtonBox, QStatusBar,
    QFontComboBox, QSpinBox, QComboBox, QColorDialog, QFontDialog)
from PySide6.QtGui import QPalette, QColor, QAction, QIcon, QFont, QTextCharFormat, QActionGroup, QTextCursor
from PySide6.QtCore import Qt, QTimer
import os, sys
from datetime import datetime
from core.theme_manager import ThemeManager, Theme
from core.voice_manager import VoiceManager
from core.splash_screen import SplashScreen

# Create a simple red square icon for the system tray
def create_app_icon():
    from PySide6.QtGui import QPixmap, QPainter, QColor
    icon = QPixmap(32, 32)
    icon.fill(Qt.transparent)
    painter = QPainter(icon)
    painter.fillRect(4, 4, 24, 24, QColor("#c41e3a"))  # Dark red color
    painter.end()
    return QIcon(icon)


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

def show_status_message(self, message, timeout=3000):
    """Show a message in the status bar"""
    self.statusBar().showMessage(message, timeout)

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
        
        # Show splash screen
        self.splash = SplashScreen()
        self.splash.show()
        
        # Initialize voice manager (but don't start listening yet)
        self.voice_manager = VoiceManager()
        self.voice_manager.voice_command_received.connect(self.handle_voice_command)
        self.voice_manager.recording_started.connect(self.on_recording_started)
        self.voice_manager.recording_stopped.connect(self.on_recording_stopped)
        self.voice_manager.error_occurred.connect(self.on_voice_error)
        self.voice_manager.recording_stopped.connect(lambda: self.statusBar().showMessage("Processing..."))
        self.voice_manager.error_occurred.connect(lambda msg: self.statusBar().showMessage(f"Error: {msg}", 5000))
        
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
        
    def handle_voice_command(self, command):
        """Handle voice commands received from VoiceManager"""
        try:
            action = self.voice_manager.process_command(command)
            feedback = f"Voice command: {command}"
            
            try:
                # File operations
                if action == "new":
                    self.new_note()
                elif action == "save":
                    self.save_note()
                elif action == "list":
                    self.list_notes()
                elif action == "clear":
                    self.text_edit.clear()
                elif action == "quit":
                    self.close()
                
                # Text formatting
                elif action == "format:bold":
                    self.toggle_bold()
                elif action == "format:italic":
                    self.toggle_italic()
                elif action == "format:normal":
                    format = self.text_edit.currentCharFormat()
                    format.setFontWeight(QFont.Normal)
                    format.setFontItalic(False)
                    self.text_edit.setCurrentCharFormat(format)
                elif action.startswith("format:size:"):
                    size = int(action.split(":")[-1])
                    self.text_edit.setFontPointSize(size)
                elif action.startswith("format:color:"):
                    color_name = action.split(":")[-1]
                    self.text_edit.setTextColor(QColor(color_name))
                elif action.startswith("format:title:"):
                    text = action.split(":", 2)[-1]
                    format = self.text_edit.currentCharFormat()
                    format.setFontPointSize(24)
                    format.setFontWeight(QFont.Bold)
                    self.text_edit.setCurrentCharFormat(format)
                    self.text_edit.insertPlainText(text + "\n")
                elif action.startswith("format:heading:"):
                    text = action.split(":", 2)[-1]
                    format = self.text_edit.currentCharFormat()
                    format.setFontPointSize(18)
                    format.setFontWeight(QFont.Bold)
                    self.text_edit.setCurrentCharFormat(format)
                    self.text_edit.insertPlainText(text + "\n")
                
                # Navigation and text operations
                elif action == "nav:page_up":
                    self.text_edit.moveCursor(QTextCursor.PreviousPage)
                elif action == "nav:page_down":
                    self.text_edit.moveCursor(QTextCursor.NextPage)
                elif action == "nav:top":
                    self.text_edit.moveCursor(QTextCursor.Start)
                elif action == "nav:bottom":
                    self.text_edit.moveCursor(QTextCursor.End)
                elif action == "nav:select_all":
                    self.text_edit.selectAll()
                elif action == "nav:copy":
                    self.text_edit.copy()
                elif action == "nav:paste":
                    self.text_edit.paste()
                elif action == "nav:undo":
                    self.text_edit.undo()
                elif action == "nav:redo":
                    self.text_edit.redo()
                elif action.startswith("nav:find:"):
                    text = action.split(":", 2)[-1]
                    self.text_edit.find(text)
                
                # Text-to-speech commands
                elif action == "read:all":
                    self.voice_manager.speak_text(self.text_edit.toPlainText())
                elif action == "read:selection":
                    text = self.text_edit.textCursor().selectedText()
                    if text:
                        self.voice_manager.speak_text(text)
                    else:
                        self.show_status_message("No text selected", 3000)
                elif action == "read:stop":
                    self.voice_manager.stop_speaking()
                elif action == "read:pause":
                    # Pause functionality will be implemented when supported
                    self.show_status_message("Pause reading not yet supported", 3000)
                elif action == "read:resume":
                    # Resume functionality will be implemented when supported
                    self.show_status_message("Resume reading not yet supported", 3000)
                
                # Show dialogs
                elif action == "show:about":
                    self.show_about()
                elif action == "show:help":
                    self.show_voice_commands()
                elif action == "show:credits":
                    self.show_credits()
                
                # Text insertion
                elif action.startswith("text:"):
                    text = action[5:]
                    self.text_edit.insertPlainText(text + " ")
                
                # Show feedback in status bar
                self.show_status_message(feedback)
            
            except Exception as e:
                self.show_status_message(f"Error executing command: {str(e)}", 5000)
                print(f"Error executing voice command: {str(e)}")
        
        except Exception as e:
            self.show_status_message("Error processing voice command", 3000)
            print(f"Error in voice command handling: {str(e)}")
    
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
        
        voice_help_action = QAction("🎤 &Voice Commands", self)
        voice_help_action.setStatusTip("Learn about available voice commands")
        voice_help_action.triggered.connect(self.show_voice_commands)
        voice_help_action.setShortcut("F1")
        help_menu.addAction(voice_help_action)
        
        help_menu.addSeparator()
        
        terms_action = QAction("&Terms && Conditions", self)
        terms_action.triggered.connect(self.show_terms)
        help_menu.addAction(terms_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About DurangDBack", self)
        about_action.setStatusTip("Learn more about DurangDBack")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        credits_action = QAction("&Credits", self)
        credits_action.setStatusTip("View development team and acknowledgments")
        credits_action.triggered.connect(self.show_credits)
        help_menu.addAction(credits_action)
        
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
        
        # Add separator
        toolbar.addSeparator()
        
        # Voice buttons layout
        voice_toolbar = QToolBar()
        voice_toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 0px;
                border: none;
            }
        """)
        
        # Voice command button (Press to talk)
        self.voice_btn = QPushButton("🎤")  # Microphone emoji
        self.voice_btn.setStatusTip("Press and hold to give voice commands")
        self.voice_btn.setFixedSize(32, 32)  # Make it square
        self.voice_btn.setStyleSheet("""
            QPushButton {
                border-radius: 16px;
                background-color: #444;
                color: white;
                font-size: 16px;
                padding: 0px;
                margin: 0px 2px;
            }
            QPushButton:pressed {
                background-color: #c41e3a;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        # Use press and release events instead of toggle
        self.voice_btn.pressed.connect(self.start_voice_assistant)
        self.voice_btn.released.connect(self.stop_voice_assistant)
        voice_toolbar.addWidget(self.voice_btn)
        
        # Text-to-speech button
        self.speak_btn = QPushButton("🔊")  # Speaker emoji
        self.speak_btn.setCheckable(True)
        self.speak_btn.setStatusTip("Read note aloud")
        self.speak_btn.setFixedSize(32, 32)
        self.speak_btn.setStyleSheet("""
            QPushButton {
                border-radius: 16px;
                background-color: #444;
                color: white;
                font-size: 16px;
                padding: 0px;
                margin: 0px 2px;
            }
            QPushButton:checked {
                background-color: #006400;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:checked:hover {
                background-color: #008000;
            }
        """)
        self.speak_btn.clicked.connect(self.toggle_text_to_speech)
        voice_toolbar.addWidget(self.speak_btn)
        
        # Add voice toolbar to main toolbar
        toolbar.addSeparator()
        toolbar.addWidget(voice_toolbar)
    
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
            
    def start_voice_assistant(self):
        """Start voice assistant when button is pressed"""
        try:
            if not hasattr(self, 'voice_manager'):
                self.voice_manager = VoiceManager()
                self.voice_manager.voice_command_received.connect(self.handle_voice_command)
                self.voice_manager.recording_started.connect(self.on_recording_started)
                self.voice_manager.recording_stopped.connect(self.on_recording_stopped)
                self.voice_manager.error_occurred.connect(self.on_voice_error)
                self.voice_manager.speech_started.connect(self.on_speech_started)
                self.voice_manager.speech_finished.connect(self.on_speech_finished)

            # Show help message for first-time users
            if not hasattr(self, '_voice_help_shown'):
                self._voice_help_shown = True
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Voice Commands Available")
                msg.setText("Voice assistant is ready! Would you like to see available voice commands?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                if msg.exec() == QMessageBox.Yes:
                    self.show_voice_commands()
            
            # Start listening
            self.voice_manager.start_listening()
            self.statusBar().showMessage("Listening for command - Release button when done")
        except Exception as e:
            self.statusBar().showMessage(f"Failed to start voice assistant: {str(e)}", 5000)
            print(f"Error starting voice assistant: {str(e)}")
    
    def stop_voice_assistant(self):
        """Stop voice assistant when button is released"""
        try:
            if hasattr(self, 'voice_manager'):
                self.voice_manager.stop_listening()
            self.statusBar().showMessage("Processing command...")
        except Exception as e:
            self.statusBar().showMessage(f"Error stopping voice assistant: {str(e)}", 5000)
            print(f"Error stopping voice assistant: {str(e)}")
    
    def toggle_text_to_speech(self):
        """Toggle reading the note aloud"""
        try:
            if not hasattr(self, 'voice_manager'):
                self.voice_manager = VoiceManager()
                self.voice_manager.speech_started.connect(self.on_speech_started)
                self.voice_manager.speech_finished.connect(self.on_speech_finished)
            
            if self.speak_btn.isChecked():
                # Get selected text or all text
                text = self.text_edit.textCursor().selectedText()
                if not text:
                    text = self.text_edit.toPlainText()
                
                if text:
                    self.voice_manager.speak_text(text)
                    self.statusBar().showMessage("Reading text aloud...")
                else:
                    self.speak_btn.setChecked(False)
                    self.statusBar().showMessage("No text to read", 3000)
            else:
                self.voice_manager.stop_speaking()
                self.statusBar().showMessage("Stopped reading", 3000)
        except Exception as e:
            self.speak_btn.setChecked(False)
            self.statusBar().showMessage(f"Error in text-to-speech: {str(e)}", 5000)
            print(f"Error in text-to-speech: {str(e)}")
    
    def on_speech_started(self):
        """Handle speech started signal"""
        self.speak_btn.setChecked(True)
        self.speak_btn.setStatusTip("Click to stop reading")
    
    def on_speech_finished(self):
        """Handle speech finished signal"""
        self.speak_btn.setChecked(False)
        self.speak_btn.setStatusTip("Read note aloud")
        self.statusBar().showMessage("Finished reading", 3000)
            
    def on_recording_started(self):
        """Handle recording started signal"""
        try:
            self.statusBar().showMessage("Listening...")
            if hasattr(self, 'voice_btn'):
                self.voice_btn.setStyleSheet(self.voice_btn.styleSheet() + "QPushButton:checked { background-color: #00ff00; }")
        except Exception as e:
            print(f"Error in recording started handler: {str(e)}")
        
    def on_recording_stopped(self):
        """Handle recording stopped signal"""
        try:
            self.statusBar().showMessage("Processing...")
            if hasattr(self, 'voice_btn'):
                self.voice_btn.setStyleSheet(self.voice_btn.styleSheet().replace("background-color: #00ff00;", "background-color: #c41e3a;"))
        except Exception as e:
            print(f"Error in recording stopped handler: {str(e)}")
        
    def on_voice_error(self, error_msg):
        """Handle voice recognition errors"""
        try:
            self.statusBar().showMessage(f"Error: {error_msg}", 5000)
            if hasattr(self, 'voice_btn'):
                self.voice_btn.setChecked(False)
            if hasattr(self, 'voice_manager'):
                self.voice_manager.stop_listening()
        except Exception as e:
            print(f"Error in voice error handler: {str(e)}")
            
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
        about_text = """
        <div style='text-align: center;'>
            <h2>DurangDBack Notepad</h2>
            <h4>Version 1.0.0</h4>
            <p>A professional note-taking application with voice commands and automatic backups.</p>
            <hr>
            <p><b>Created by Chsiom Eke</b><br>
            Brand Owner of Quick Red Tech</p>
            <hr>
            <h4>Features:</h4>
            <ul style='list-style-type: none; padding: 0;'>
                <li>✍️ Rich Text Editing</li>
                <li>🎤 Voice Commands</li>
                <li>💾 Automatic Backups</li>
                <li>🎨 Custom Themes</li>
                <li>📝 Multiple Font Styles</li>
                <li>🔄 Auto-Save</li>
            </ul>
            <p><small>Copyright © 2025 Quick Red Tech. All rights reserved.</small></p>
        </div>
        """
        QMessageBox.about(self, "About DurangDBack", about_text)

    def show_voice_commands(self):
        """Show available voice commands in a dialog"""
        commands_text = """
        <div style='font-family: Segoe UI, Arial, sans-serif;'>
            <h2 style='color: #c41e3a; text-align: center;'>🎤 Voice Commands Guide</h2>
            
            <div style='margin: 10px 0;'>
                <h3 style='color: #444;'>📝 File Operations</h3>
                <ul>
                    <li><b>"new note"</b> or <b>"create note"</b> - Start a new note</li>
                    <li><b>"save note"</b> or <b>"save this"</b> - Save current note</li>
                    <li><b>"list notes"</b> or <b>"show notes"</b> - View saved notes</li>
                    <li><b>"clear note"</b> or <b>"clear all"</b> - Clear current note</li>
                </ul>
            </div>

            <div style='margin: 10px 0;'>
                <h3 style='color: #444;'>🎨 Text Formatting</h3>
                <ul>
                    <li><b>"make bold"</b> or <b>"bold text"</b> - Make text bold</li>
                    <li><b>"make italic"</b> or <b>"italicize"</b> - Make text italic</li>
                    <li><b>"regular text"</b> or <b>"normal text"</b> - Reset formatting</li>
                    <li><b>"font size [number]"</b> - Change text size (e.g., "font size 16")</li>
                    <li><b>"color [name]"</b> - Change text color (e.g., "color red")</li>
                </ul>
            </div>

            <div style='margin: 10px 0;'>
                <h3 style='color: #444;'>⌨️ Navigation & Editing</h3>
                <ul>
                    <li><b>"go to top"</b> or <b>"scroll up"</b> - Move to start</li>
                    <li><b>"go to bottom"</b> or <b>"scroll down"</b> - Move to end</li>
                    <li><b>"select all"</b> - Select all text</li>
                    <li><b>"copy"</b> or <b>"paste"</b> - Copy/paste text</li>
                    <li><b>"undo"</b> or <b>"redo"</b> - Undo/redo changes</li>
                </ul>
            </div>

            <div style='margin: 10px 0;'>
                <h3 style='color: #444;'>📄 Special Formatting</h3>
                <ul>
                    <li><b>"title: [text]"</b> - Create large title</li>
                    <li><b>"heading: [text]"</b> - Create section heading</li>
                    <li><b>"new line"</b> or <b>"new paragraph"</b> - Insert line break</li>
                    <li><b>"insert date"</b> or <b>"insert time"</b> - Add current date/time</li>
                </ul>
            </div>

            <div style='margin: 10px 0;'>
                <h3 style='color: #444;'>🔄 App Control</h3>
                <ul>
                    <li><b>"about"</b> - Show app information</li>
                    <li><b>"help"</b> - Show this help guide</li>
                    <li><b>"credits"</b> - Show development credits</li>
                    <li><b>"quit app"</b> or <b>"exit"</b> - Close the application</li>
                </ul>
            </div>

            <div style='margin: 10px 0; text-align: center; color: #666;'>
                <p><i>💡 Tip: Click the microphone button 🎤 to start/stop voice recognition</i></p>
                <p><i>🗣️ Any other spoken text will be inserted into your note</i></p>
            </div>
        </div>
        """
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Voice Commands Help")
        help_dialog.setMinimumWidth(500)
        help_dialog.setMinimumHeight(600)

        layout = QVBoxLayout()
        text_browser = QTextEdit()
        text_browser.setReadOnly(True)
        text_browser.setHtml(commands_text)
        layout.addWidget(text_browser)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(help_dialog.accept)
        layout.addWidget(close_btn)

        help_dialog.setLayout(layout)
        help_dialog.exec()

    def show_credits(self):
        credits_text = """
        <div style='text-align: center;'>
            <h2>Credits & Acknowledgments</h2>
            <hr>
            <h4>Development Team:</h4>
            <p><b>Lead Developer & Designer:</b><br>
            Chsiom Eke<br>
            <small>Quick Red Tech</small></p>
            
            <h4>Technologies Used:</h4>
            <ul style='list-style-type: none; padding: 0;'>
                <li><b>UI Framework:</b> PySide6 (Qt)</li>
                <li><b>Voice Recognition:</b> SpeechRecognition</li>
                <li><b>Theme Engine:</b> Custom QT Theming</li>
            </ul>
            
            <h4>Special Thanks:</h4>
            <p>To the open source community and<br>
            all Quick Red Tech team members</p>
            
            <hr>
            <p><small>DurangDBack is a product of Quick Red Tech<br>
            Developed with ❤️ by Chsiom Eke</small></p>
        </div>
        """
        QMessageBox.about(self, "Credits - DurangDBack", credits_text)

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
    window = DurangMain()
    
    # Handle application shutdown
    def cleanup():
        try:
            if hasattr(window, 'voice_manager'):
                try:
                    window.voice_manager.stop_listening()
                except Exception as e:
                    print(f"Error stopping voice manager during cleanup: {str(e)}")
            
            if hasattr(window, 'voice_btn'):
                try:
                    window.voice_btn.setChecked(False)
                except Exception as e:
                    print(f"Error resetting voice button during cleanup: {str(e)}")
        except Exception as e:
            print(f"Error during application cleanup: {str(e)}")
    
    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec())