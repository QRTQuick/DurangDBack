import speech_recognition as sr
import threading
from PySide6.QtCore import QObject, Signal
import queue
import time

class VoiceManager(QObject):
    """Manages voice recognition functionality"""
    
    # Signals for UI updates
    voice_command_received = Signal(str)  # Emitted when a voice command is recognized
    recording_started = Signal()          # Emitted when recording starts
    recording_stopped = Signal()          # Emitted when recording stops
    error_occurred = Signal(str)          # Emitted when an error occurs
    
    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.command_queue = queue.Queue()
        self.mic = None
        
    def start_listening(self):
        """Start background listening for voice commands"""
        if not self.is_listening:
            self.is_listening = True
            threading.Thread(target=self._listen_loop, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.is_listening = False
        if self.mic:
            self.mic.__exit__(None, None, None)
    
    def _listen_loop(self):
        """Background loop that listens for voice commands"""
        while self.is_listening:
            try:
                with sr.Microphone() as source:
                    self.mic = source
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    while self.is_listening:
                        try:
                            self.recording_started.emit()
                            audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                            self.recording_stopped.emit()
                            
                            try:
                                text = self.recognizer.recognize_google(audio)
                                if text:
                                    self.voice_command_received.emit(text.lower())
                            except sr.UnknownValueError:
                                pass  # Speech was unclear
                            except sr.RequestError as e:
                                self.error_occurred.emit(f"Could not request results: {str(e)}")
                                
                        except sr.WaitTimeoutError:
                            pass  # No speech detected, continue listening
                            
            except Exception as e:
                self.error_occurred.emit(f"Error initializing microphone: {str(e)}")
                time.sleep(2)  # Wait before retrying
    
    def process_command(self, command):
        """Process a voice command and return the action to take"""
        # Basic command processing
        command = command.lower()
        
        if "new note" in command:
            return "new"
        elif "save note" in command or "save" in command:
            return "save"
        elif "list notes" in command or "show notes" in command:
            return "list"
        elif "clear" in command:
            return "clear"
        elif "quit" in command or "exit" in command:
            return "quit"
        
        # If no command matches, treat as note text
        return "text:" + command