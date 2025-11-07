import os
import shutil
from datetime import datetime


class NoteManager:
    def __init__(self):
        self.notes_path = os.path.join(os.getcwd(), "notes")
        self.backup_path = os.path.join(os.getcwd(), "backup")
        os.makedirs(self.notes_path, exist_ok=True)
        os.makedirs(self.backup_path, exist_ok=True)

    def list_notes(self):
        return [f for f in os.listdir(self.notes_path) if f.endswith(".txt")]

    def generate_filename(self):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"note_{now}.txt"

    def save_note(self, filename, content):
        filepath = os.path.join(self.notes_path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        shutil.copy(filepath, os.path.join(self.backup_path, filename))
        return filepath

    def load_note(self, filename):
        filepath = os.path.join(self.notes_path, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        raise FileNotFoundError("Note not found")