from PySide6.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QTimer

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Create a pixmap for the splash screen
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap)
        
        # Create the main layout widget
        self.content = QWidget(self)
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title = QLabel("DurangDBack")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Add subtitle
        subtitle = QLabel("Professional Note Taking with Voice Commands")
        subtitle.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 14px;
            }
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Add progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #c82828;
                border-radius: 3px;
            }
        """)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)
        
        # Add status label
        self.status = QLabel("Loading...")
        self.status.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 12px;
            }
        """)
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)
        
        # Position the content widget
        self.content.setGeometry(0, 0, 400, 300)
        
        # Setup fade effect
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def drawContents(self, painter):
        # Draw background with rounded corners
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw dark background
        painter.setBrush(QColor(45, 45, 45))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
    def update_progress(self, value, status=""):
        """Update progress bar and status message"""
        self.progress.setValue(value)
        if status:
            self.status.setText(status)
            
    def start_loading(self):
        """Simulate loading process"""
        self.show()
        
        # Setup progress updates
        def update(step):
            if step <= 100:
                status_messages = {
                    20: "Initializing application...",
                    40: "Loading user interface...",
                    60: "Setting up voice recognition...",
                    80: "Preparing workspace...",
                    100: "Ready to start!"
                }
                self.update_progress(step, status_messages.get(step, ""))
                if step < 100:
                    QTimer.singleShot(50, lambda: update(step + 1))
                else:
                    QTimer.singleShot(500, self.close)
                    
        QTimer.singleShot(0, lambda: update(0))