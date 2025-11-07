import speech_recognition as sr
import threading
from PySide6.QtCore import QObject, Signal
import queue
import time
import pyttsx3

class VoiceManager(QObject):
    """Manages voice recognition and text-to-speech functionality"""
    
    # Signals for UI updates
    voice_command_received = Signal(str)  # Emitted when a voice command is recognized
    recording_started = Signal()          # Emitted when recording starts
    recording_stopped = Signal()          # Emitted when recording stops
    error_occurred = Signal(str)          # Emitted when an error occurs
    speech_started = Signal()             # Emitted when text-to-speech starts
    speech_finished = Signal()            # Emitted when text-to-speech finishes
    
    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.command_queue = queue.Queue()
        self.mic = None
        self._mic_context = None  # Store the microphone context manager
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speed of speech
        self.is_speaking = False
        self.should_stop_speaking = False
        
        # Configure voice properties
        voices = self.engine.getProperty('voices')
        # Try to set a female voice if available
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
    def speak_text(self, text):
        """Read text using text-to-speech"""
        try:
            if self.is_speaking:
                self.stop_speaking()
            
            self.is_speaking = True
            self.should_stop_speaking = False
            self.speech_started.emit()
            
            def speak_thread():
                try:
                    def on_word(name, location, length):
                        return not self.should_stop_speaking
                    
                    self.engine.connect('started-word', on_word)
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"Error in speech thread: {str(e)}")
                finally:
                    self.is_speaking = False
                    self.speech_finished.emit()
            
            threading.Thread(target=speak_thread, daemon=True).start()
            
        except Exception as e:
            print(f"Error starting speech: {str(e)}")
            self.is_speaking = False
            self.speech_finished.emit()
    
    def stop_speaking(self):
        """Stop text-to-speech"""
        if self.is_speaking:
            self.should_stop_speaking = True
            self.engine.stop()
            self.is_speaking = False
    
    def start_listening(self):
        """Start background listening for voice commands"""
        try:
            # Stop any existing listening session first
            if self.is_listening:
                self.stop_listening()
            
            # Clear any previous state
            self._mic_context = None
            self.mic = None
            
            # Start new listening session
            self.is_listening = True
            thread = threading.Thread(target=self._listen_loop, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"Error in start_listening: {str(e)}")
            self.is_listening = False
            self._mic_context = None
            self.mic = None
            raise  # Re-raise the error for proper handling
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        try:
            # Set flag first to prevent new operations
            self.is_listening = False
            
            # Clean up microphone resources
            try:
                if self._mic_context:
                    self._mic_context.__exit__(None, None, None)
            except Exception as e:
                print(f"Error closing microphone context: {str(e)}")
            finally:
                # Always reset these
                self._mic_context = None
                self.mic = None
                
        except Exception as e:
            print(f"Error in stop_listening: {str(e)}")
            # Ensure flags are reset even if cleanup fails
            self.is_listening = False
            self._mic_context = None
            self.mic = None
    
    def _listen_loop(self):
        """Background loop that listens for voice commands"""
        while self.is_listening:
            try:
                # Create and store the microphone context manager
                self._mic_context = sr.Microphone().__enter__()
                self.mic = self._mic_context
                
                try:
                    self.recognizer.adjust_for_ambient_noise(self.mic, duration=0.5)
                except Exception as e:
                    self.error_occurred.emit(f"Error adjusting for noise: {str(e)}")
                    continue
                
                while self.is_listening:
                    if not self.mic or not self._mic_context:
                        break
                    
                    try:
                        self.recording_started.emit()
                        try:
                            audio = self.recognizer.listen(self.mic, timeout=5, phrase_time_limit=10)
                            if not self.is_listening:  # Check if we should stop
                                break
                            self.recording_stopped.emit()
                            
                            try:
                                text = self.recognizer.recognize_google(audio)
                                if text and self.is_listening:  # Check again before emitting
                                    self.voice_command_received.emit(text.lower())
                            except sr.UnknownValueError:
                                pass  # Speech was unclear
                            except sr.RequestError as e:
                                self.error_occurred.emit(f"Could not request results: {str(e)}")
                            
                        except sr.WaitTimeoutError:
                            pass  # No speech detected, continue listening
                            
                    except Exception as e:
                        if self.is_listening:  # Only emit error if still listening
                            self.error_occurred.emit(f"Error during listening: {str(e)}")
                        break  # Break inner loop to reinitialize microphone
                
            except Exception as e:
                if self.is_listening:  # Only emit error if still listening
                    self.error_occurred.emit(f"Error initializing microphone: {str(e)}")
                time.sleep(2)  # Wait before retrying
            
            finally:
                # Clean up microphone in case of any errors
                try:
                    if self._mic_context:
                        self._mic_context.__exit__(None, None, None)
                except Exception:
                    pass  # Ignore cleanup errors
                self._mic_context = None
                self.mic = None
    
    def process_command(self, command):
        """Process a voice command and return the action to take"""
        # Basic command processing
        command = command.lower().strip()
        
        # Reading commands
        if any(phrase in command for phrase in ["read note", "read text", "read this"]):
            return "read:all"
        elif any(phrase in command for phrase in ["read selection", "read selected"]):
            return "read:selection"
        elif "stop reading" in command or "stop speaking" in command:
            return "read:stop"
        elif "pause reading" in command or "pause speaking" in command:
            return "read:pause"
        elif "resume reading" in command or "continue reading" in command:
            return "read:resume"
            
        # Navigation commands
        elif any(phrase in command for phrase in ["page up", "scroll up", "previous page"]):
            return "nav:page_up"
        elif any(phrase in command for phrase in ["page down", "scroll down", "next page"]):
            return "nav:page_down"
        elif "beginning" in command or "start of document" in command:
            return "nav:top"
        elif "end" in command or "end of document" in command:
            return "nav:bottom"
        elif any(phrase in command for phrase in ["select all", "select everything"]):
            return "nav:select_all"
        elif any(phrase in command for phrase in ["copy text", "copy this"]):
            return "nav:copy"
        elif any(phrase in command for phrase in ["paste text", "paste here"]):
            return "nav:paste"
        elif "undo" in command or "undo that" in command:
            return "nav:undo"
        elif "redo" in command or "redo that" in command:
            return "nav:redo"
        elif "find" in command or "search for" in command:
            # Extract search term
            search_term = command.split("find")[-1].strip() if "find" in command else command.split("search for")[-1].strip()
            if search_term:
                return f"nav:find:{search_term}"
        
        # File operations
        elif any(phrase in command for phrase in ["new note", "create note", "start note"]):
            return "new"
        elif any(phrase in command for phrase in ["save note", "save this", "save document", "save"]):
            return "save"
        elif any(phrase in command for phrase in ["list notes", "show notes", "display notes", "all notes"]):
            return "list"
        elif any(phrase in command for phrase in ["clear note", "clear all", "clear text", "erase all"]):
            return "clear"
        
        # Text formatting
        elif any(phrase in command for phrase in ["make bold", "bold text", "set bold"]):
            return "format:bold"
        elif any(phrase in command for phrase in ["make italic", "italicize", "set italic"]):
            return "format:italic"
        elif any(phrase in command for phrase in ["regular text", "normal text", "plain text"]):
            return "format:normal"
        elif "font size" in command:
            # Extract number from command
            import re
            sizes = re.findall(r'\d+', command)
            if sizes:
                return f"format:size:{sizes[0]}"
            
        # Color commands
        elif "color red" in command:
            return "format:color:red"
        elif "color blue" in command:
            return "format:color:blue"
        elif "color green" in command:
            return "format:color:green"
        elif "color black" in command:
            return "format:color:black"
        elif "color" in command:
            # Try to extract color name
            words = command.split()
            if len(words) > 1 and "color" in words:
                color_index = words.index("color") + 1
                if color_index < len(words):
                    return f"format:color:{words[color_index]}"
        
        # App control
        elif any(phrase in command for phrase in ["quit app", "exit app", "close app", "quit", "exit"]):
            return "quit"
        elif "about" in command:
            return "show:about"
        elif "help" in command:
            return "show:help"
        elif "credits" in command:
            return "show:credits"
        
        # Special formatting
        elif any(phrase in command for phrase in ["new line", "new paragraph", "line break"]):
            return "text:\n"
        elif command.startswith("title:"):
            return f"format:title:{command[6:]}"
        elif command.startswith("heading:"):
            return f"format:heading:{command[8:]}"
        
        # Date/Time insertion
        elif any(phrase in command for phrase in ["insert date", "add date", "current date"]):
            from datetime import datetime
            return f"text:{datetime.now().strftime('%Y-%m-%d')}"
        elif any(phrase in command for phrase in ["insert time", "add time", "current time"]):
            from datetime import datetime
            return f"text:{datetime.now().strftime('%H:%M:%S')}"
        
        # If no command matches, treat as note text
        return "text:" + command