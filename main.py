# main.py
import logging
import datetime
import time

from utils import load_config, get_last_run_timestamp, save_last_run_timestamp
from readwise_client import ReadwiseClient
from anki_client import AnkiClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_sync():
    logging.info("Starting Readwise to Anki sync process...")
    try:
        config = load_config()
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        return

    readwise = ReadwiseClient(token=config["readwise_token"])
    anki = AnkiClient(
        connect_url=config["anki_connect_url"],
        deck_name=config["anki_deck_name"],
        model_name=config["anki_model_name"],
        app_path=config["anki_app_path"]
    )

    # 0. Validate Readwise token first
    if not readwise.check_token():
        logging.error("Halting due to invalid Readwise token.")
        return

    # 1. Get last run timestamp
    last_run_iso = get_last_run_timestamp(config.get("last_run_file"))
    
    # Record the time *before* fetching from Readwise for the next `last_run_timestamp`
    # This ensures that any highlights created during the script's execution are picked up next time.
    # Use UTC for consistency.
    current_run_timestamp_for_next_run = datetime.datetime.now(datetime.timezone.utc)


    # 2. Fetch new highlights from Readwise
    try:
        all_data = readwise.fetch_highlights(updated_after=last_run_iso)
    except Exception as e:
        logging.error(f"Failed to fetch highlights from Readwise: {e}")
        return # Don't update last_run_timestamp if fetch fails

    if not all_data:
        logging.info("No new book/article data from Readwise.")
        save_last_run_timestamp(config.get("last_run_file")) # Save current time as last run even if no new data
        return

    # 3. Parse for dictionary definitions
    definitions = readwise.parse_dictionary_definitions(all_data)

    if not definitions:
        logging.info("No new dictionary definitions found in the fetched highlights.")
        save_last_run_timestamp(config.get("last_run_file")) # Save current time as last run
        return

    logging.info(f"Found {len(definitions)} new dictionary definitions to add to Anki.")

    # 4. Check Anki status and launch if necessary
    if not anki.is_anki_running_and_responsive():
        logging.info("Anki is not running or AnkiConnect is not responsive. Attempting to launch Anki...")
        if not anki.launch_anki():
            logging.error("Failed to launch Anki or Anki is still not responsive. Skipping Anki additions for this run.")
            # Do NOT save last_run_timestamp here, so we retry these highlights next time.
            return 
        
        # Re-check after attempting launch and waiting
        if not anki.is_anki_running_and_responsive():
            logging.error("Anki is still not responsive after launch attempt. Skipping Anki additions.")
            # Do NOT save last_run_timestamp here.
            return
    else:
        logging.info("Anki is running and AnkiConnect is responsive.")

    # 5. Ensure Anki deck and model exist
    if not anki.ensure_deck_exists():
        logging.error(f"Failed to ensure Anki deck '{anki.deck_name}' exists. Skipping Anki additions.")
        # Do NOT save last_run_timestamp here.
        return
    
    if not anki.ensure_model_exists():
        logging.error(f"Anki model '{anki.model_name}' does not exist or is misconfigured. Please check Anki. Skipping Anki additions.")
        # Do NOT save last_run_timestamp here.
        return

    # 6. Add definitions to Anki
    notes_added_count = 0
    notes_failed_count = 0
    for entry in definitions:
        note_id = anki.add_note_to_anki(
            word=entry["word"],
            word_type=entry["type"],
            definition=entry["definition"],
            source_title=entry["source_title"],
            source_author=entry["source_author"],
            readwise_url=entry["readwise_highlight_url"],
            highlight_id=entry["highlight_id"]
        )
        if note_id:
            notes_added_count += 1
        else:
            notes_failed_count +=1
            logging.warning(f"Could not add note for word: {entry['word']}")
    
    logging.info(f"Finished processing definitions. Added: {notes_added_count}, Failed: {notes_failed_count}.")

    # 7. Save last run timestamp if there were no major errors preventing processing some highlights
    # If all notes failed, we might not want to update the timestamp.
    # However, if some succeeded, we should update it.
    # For simplicity now, if we reached this point and attempted additions, we update the timestamp.
    # More granular error handling could decide not to save if all Anki additions failed.
    if notes_failed_count > 0 and notes_added_count == 0 and len(definitions) > 0:
        logging.warning("No notes were successfully added to Anki, though definitions were found. Last run timestamp will NOT be updated to retry.")
    else:
        # Save the timestamp that was taken *before* the Readwise API call
        save_last_run_timestamp(config.get("last_run_file"))
        
    logging.info("Readwise to Anki sync process finished.")


if __name__ == "__main__":
    run_sync()