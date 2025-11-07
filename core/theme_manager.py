from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from enum import Enum

class Theme(Enum):
    DARK_RED = "Dark Red"
    DARK_BLUE = "Dark Blue"
    DARK_GREEN = "Dark Green"
    LIGHT = "Light"
    SYSTEM = "System"

class ThemeManager:
    @staticmethod
    def apply_theme(app, theme=Theme.DARK_RED):
        if theme == Theme.SYSTEM:
            app.setPalette(app.style().standardPalette())
            return

        palette = QPalette()
        
        if theme == Theme.LIGHT:
            # Light theme colors
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
            palette.setColor(QPalette.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.Link, QColor(0, 100, 200))
            accent = QColor(0, 120, 215)
        else:
            # Dark theme base
            palette.setColor(QPalette.Window, QColor(45, 45, 45))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(30, 30, 30))
            palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(60, 60, 60))
            palette.setColor(QPalette.ButtonText, Qt.white)
            
            # Theme-specific accent colors
            if theme == Theme.DARK_RED:
                accent = QColor(200, 40, 40)
                palette.setColor(QPalette.Link, QColor(255, 80, 80))
            elif theme == Theme.DARK_BLUE:
                accent = QColor(40, 120, 200)
                palette.setColor(QPalette.Link, QColor(80, 160, 255))
            elif theme == Theme.DARK_GREEN:
                accent = QColor(40, 180, 40)
                palette.setColor(QPalette.Link, QColor(80, 255, 80))

        # Common theme properties
        palette.setColor(QPalette.Highlight, accent)
        palette.setColor(QPalette.HighlightedText, Qt.white if theme != Theme.LIGHT else Qt.black)
        palette.setColor(QPalette.Disabled, QPalette.Text, Qt.gray)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.gray)

        app.setPalette(palette)
        
    @staticmethod
    def get_theme_stylesheet(theme=Theme.DARK_RED):
        """Returns additional stylesheet customizations for the theme"""
        if theme == Theme.LIGHT:
            return """
                QToolTip { 
                    color: #000000; 
                    background-color: #ffffff; 
                    border: 1px solid #505050; 
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 2px;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """
        
        # Dark theme variations
        accent_color = {
            Theme.DARK_RED: "#c82828",
            Theme.DARK_BLUE: "#2878c8",
            Theme.DARK_GREEN: "#28c828",
        }.get(theme, "#c82828")  # Default to red
        
        return f"""
            QToolTip {{ 
                color: #ffffff; 
                background-color: #2a2a2a; 
                border: 1px solid #505050; 
            }}
            QTextEdit {{
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 2px;
                selection-background-color: {accent_color};
            }}
            QPushButton {{
                background-color: #3c3c3c;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px 15px;
                color: #ffffff;
            }}
            QPushButton:hover {{
                background-color: #505050;
                border-color: {accent_color};
            }}
            QPushButton:pressed {{
                background-color: #2a2a2a;
            }}
            QMenuBar {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QMenuBar::item:selected {{
                background-color: {accent_color};
            }}
            QMenu {{
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #505050;
            }}
            QMenu::item:selected {{
                background-color: {accent_color};
            }}
            QStatusBar {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QToolBar {{
                background-color: #2d2d2d;
                border-bottom: 1px solid #505050;
            }}
        """