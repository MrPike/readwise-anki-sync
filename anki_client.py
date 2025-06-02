# anki_client.py
import requests
import json
import logging
import subprocess
import time
import platform

class AnkiClient:
    def __init__(self, connect_url, deck_name, model_name, app_path):
        self.connect_url = connect_url
        self.deck_name = deck_name
        self.model_name = model_name
        self.app_path = app_path

    def _anki_request(self, action, **params):
        payload = {"action": action, "version": 6, "params": params}
        try:
            response = requests.post(self.connect_url, json=payload)
            response.raise_for_status()
            response_json = response.json()
            if response_json.get('error') is not None:
                logging.error(f"AnkiConnect error for action '{action}': {response_json['error']}")
                return None
            return response_json['result']
        except requests.exceptions.ConnectionError:
            logging.error(f"Could not connect to AnkiConnect at {self.connect_url}. Is Anki running with AnkiConnect installed?")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"AnkiConnect request failed for action '{action}': {e}")
            return None
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON response from AnkiConnect for action '{action}'. Response: {response.text}")
            return None


    def is_anki_running_and_responsive(self):
        """Checks if AnkiConnect is responsive."""
        return self._anki_request("version") is not None

    def launch_anki(self):
        """Launches the Anki application."""
        if platform.system() == "Darwin": # macOS
            try:
                logging.info(f"Attempting to launch Anki from: {self.app_path}")
                subprocess.Popen(["open", self.app_path])
                logging.info("Anki launch command issued. Waiting for it to start...")
                # Wait for Anki and AnkiConnect to start up
                time.sleep(15) # Adjust as needed
                return True
            except Exception as e:
                logging.error(f"Failed to launch Anki: {e}")
                return False
        else:
            logging.warning("Anki auto-launch is only supported on macOS for this script.")
            return False

    def ensure_deck_exists(self):
        """Checks if the deck exists, creates it if not."""
        deck_names = self._anki_request("deckNames")
        if deck_names is None: # Error occurred
            return False
        if self.deck_name not in deck_names:
            logging.info(f"Deck '{self.deck_name}' not found. Creating it.")
            if self._anki_request("createDeck", deck=self.deck_name) is None:
                logging.error(f"Failed to create deck '{self.deck_name}'.")
                return False
            logging.info(f"Deck '{self.deck_name}' created successfully.")
        return True

    def ensure_model_exists(self):
        """Checks if the model exists. Does not create it, only warns."""
        model_names = self._anki_request("modelNames")
        if model_names is None:
            return False
        if self.model_name not in model_names:
            logging.error(f"Anki Model '{self.model_name}' does not exist in Anki.")
            logging.error("Please create it manually or ensure the name in .env matches an existing model.")
            return False
        
        # Optional: Check if model has required fields (e.g., 'Front', 'Back' for 'Basic')
        # This adds complexity, so keeping it simple for now.
        # model_field_names = self._anki_request("modelFieldNames", modelName=self.model_name)
        # if model_field_names is None: return False
        # required_fields = ["Front", "Back"] # For Basic model
        # if not all(field in model_field_names for field in required_fields):
        #     logging.error(f"Model '{self.model_name}' does not have the required fields (e.g., Front, Back).")
        #     return False
        return True


    def add_note_to_anki(self, word, word_type, definition, source_title, source_author, readwise_url, highlight_id):
        """Adds a new note to Anki, checking for duplicates based on Word and Deck."""
        
        # Check for duplicates: A simple check based on the word in the Front field for the specific deck.
        # For more robustness, a custom field with highlight_id could be used.
        query = f'deck:"{self.deck_name}" "{self.model_name}:Front:{word}"'
        # Anki's search for exact field content is tricky. A simpler check might be to just try adding
        # and let Anki's internal duplicate handling (if configured for the model) work.
        # For now, we'll assume the user might want to control duplicates more explicitly or that the model handles it.
        # A more robust check would involve a unique ID (like highlight_id) in a custom field.

        # Let's try a simpler "findNotes" to see if a card with this front already exists.
        # This requires the front field to be named "Front" in your model.
        # If your model has a different name for the primary field, adjust this.
        
        # Using a simple approach: Check if a note with the same "word" exists.
        # This assumes "Front" is the field for the word.
        if self.model_name == "Basic": # Common model
            field_for_word_check = "Front"
        else:
            # For other models, this check might not be accurate without knowing the field names.
            # Consider adding a configuration for which field holds the "word".
            # For now, we'll skip duplicate check for non-Basic models to avoid complexity.
            logging.debug(f"Duplicate check skipped for model type '{self.model_name}'.")
            field_for_word_check = None


        if field_for_word_check:
            # AnkiConnect's findNotes returns note IDs.
            # Query needs to be specific. "Front:Word" is not standard, usually it's "FieldName:value"
            # or just "value" if searching all fields.
            # Example: findNotes query for "word" in "Front" field of a specific deck & model:
            # query = f'deck:"{self.deck_name}" note:"{self.model_name}" {field_for_word_check}:"{word}"'
            # For simplicity and broader compatibility if field names differ, we can search for the word in the context of the deck.
            # A more robust approach is to add the Readwise highlight_id as a custom field and check against that.
            
            # Simplified: Check if a note with this `highlight_id` (if available and unique) already exists.
            # This requires a field in your Anki note type dedicated to storing `readwise_highlight_id`.
            # Let's assume such a field is named 'ReadwiseHighlightID'.
            # If not, this check won't work and notes might be duplicated or update logic needed.
            # For now, we will NOT implement this advanced duplicate check based on a custom field.
            # We will just add the note. Anki itself has some duplicate prevention based on the first field for some note types.

            pass # Skipping advanced duplicate check for now.

        note = {
            "deckName": self.deck_name,
            "modelName": self.model_name,
            "fields": {
                # These field names ('Front', 'Back') must match your Anki Note Type.
                # For 'Basic' model:
                "Front": word,
                "Back": f"({word_type})<br>{definition}<hr>"
                        f"<small>Source: {source_title} (by {source_author if source_author else 'N/A'})</small><br>"
                        f"<small><a href='{readwise_url}'>View on Readwise</a> (ID: {highlight_id})</small>"
            },
            "options": {
                "allowDuplicate": False # AnkiConnect option; Anki's own duplicate handling based on model might also apply
            },
            "tags": ["readwise_import", "vocabulary"]
        }

        result = self._anki_request("addNote", note=note)
        if result:
            logging.info(f"Successfully added note to Anki: {word}")
            return result # Returns the note ID
        else:
            # Error logged by _anki_request or if result is None due to other issues
            logging.error(f"Failed to add note to Anki: {word}")
            # If error was 'cannot create note because it is a duplicate', it's not necessarily a script error.
            # The response from AnkiConnect for duplicates should be checked.
            # For now, `_anki_request` logs the error message from AnkiConnect.
            return None