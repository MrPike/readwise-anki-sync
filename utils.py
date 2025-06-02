# utils.py
import os
import datetime
from dotenv import load_dotenv
import logging

CONFIG_FILE = ".env"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Loads configuration from .env file."""
    load_dotenv(CONFIG_FILE)
    config = {
        "readwise_token": os.getenv("READWISE_API_TOKEN"),
        "anki_deck_name": os.getenv("ANKI_DECK_NAME"),
        "anki_model_name": os.getenv("ANKI_MODEL_NAME"),
        "anki_connect_url": os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765"),
        "anki_app_path": os.getenv("ANKI_APP_PATH", "/Applications/Anki.app"),
        "last_run_file": os.getenv("LAST_RUN_FILE", ".last_run")
    }
    if not config["readwise_token"]:
        logging.error("READWISE_API_TOKEN not found in .env file.")
        raise ValueError("READWISE_API_TOKEN is required.")
    if not config["anki_deck_name"]:
        logging.error("ANKI_DECK_NAME not found in .env file.")
        raise ValueError("ANKI_DECK_NAME is required.")
    if not config["anki_model_name"]:
        logging.error("ANKI_MODEL_NAME not found in .env file.")
        raise ValueError("ANKI_MODEL_NAME is required.")
    return config

def get_last_run_timestamp(last_run_file):
    """Reads the last run timestamp from .last_run file."""
    try:
        with open(last_run_file, 'r') as f:
            timestamp_str = f.read().strip()
            if timestamp_str:
                return timestamp_str
    except FileNotFoundError:
        logging.info(f"'{last_run_file}' not found. Will attempt to fetch all highlights.")
    return None

def save_last_run_timestamp(last_run_file):
    """Saves the current UTC timestamp to .last_run file."""
    # Ensure we use timezone-aware datetime object with UTC
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(last_run_file, 'w') as f:
        f.write(timestamp)
    logging.info(f"Saved last run timestamp: {timestamp}")