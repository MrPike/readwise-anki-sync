# readwise_client.py
import requests
import re
import logging
from urllib.parse import quote # For safely encoding parameters

class ReadwiseClient:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://readwise.io/api/v2"

    def _make_request(self, endpoint, params=None):
        headers = {"Authorization": f"Token {self.token}"}
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", headers=headers, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error fetching Readwise data: {e.response.status_code} {e.response.text}")
            if e.response.status_code == 401:
                 logging.error("Readwise API token is invalid or unauthorized.")
            elif e.response.status_code == 429:
                 retry_after = e.response.headers.get("Retry-After")
                 logging.warning(f"Rate limit exceeded. Retry after {retry_after} seconds.")
            raise
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error fetching Readwise data: {e}")
            raise

    def check_token(self):
        """Validates the Readwise API token."""
        headers = {"Authorization": f"Token {self.token}"}
        try:
            response = requests.get(f"{self.base_url}/auth/", headers=headers)
            if response.status_code == 204:
                logging.info("Readwise API token is valid.")
                return True
            else:
                logging.error(f"Readwise API token validation failed. Status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during Readwise token validation: {e}")
            return False


    def fetch_highlights(self, updated_after=None):
        """Fetches highlights from Readwise, optionally filtered by update date."""
        all_results = []
        next_page_cursor = None
        logging.info(f"Fetching highlights from Readwise. Updated after: {updated_after or 'beginning'}")

        while True:
            params = {}
            if next_page_cursor:
                params['pageCursor'] = next_page_cursor
            if updated_after:
                # Ensure the timestamp is properly URL-encoded if it contains special characters like '+'
                # However, ISO8601 typically doesn't, but it's good practice.
                # requests usually handles this, but being explicit can help.
                params['updatedAfter'] = updated_after

            logging.debug(f"Making export API request with params: {params}")
            try:
                data = self._make_request("export", params=params)
                all_results.extend(data.get('results', []))
                next_page_cursor = data.get('nextPageCursor')
                if not next_page_cursor:
                    break
            except requests.exceptions.RequestException:
                logging.error("Failed to fetch a page of highlights. Returning what has been gathered so far.")
                break # Or re-raise depending on desired error handling

        logging.info(f"Fetched {len(all_results)} books/articles from Readwise.")
        return all_results

    def parse_dictionary_definitions(self, readwise_data):
        """
        Parses highlights to find dictionary definitions.
        A dictionary definition looks like: word (type): definition.
        """
        definitions = []
        # Pattern: word (type): definition
        # Allows for leading/trailing spaces around components.
        # Handles potential quotes around the entire highlight from Readwise.
        pattern = re.compile(r"^(.*?)\s*\(([^)]+)\):\s*(.*)$", re.IGNORECASE)

        for book in readwise_data:
            for highlight in book.get('highlights', []):
                text = highlight.get('note', '')
                
                # Clean common quote types if they are part of the text value itself
                text_to_parse = text.strip().strip('“”"')

                match = pattern.match(text_to_parse)
                if match:
                    word, part_of_speech, definition_text = match.groups()
                    definitions.append({
                        "word": word.strip(),
                        "type": part_of_speech.strip(),
                        "definition": definition_text.strip(),
                        "source_title": book.get('title', 'N/A'),
                        "source_author": book.get('author', 'N/A'),
                        "readwise_highlight_url": highlight.get('readwise_url', ''),
                        "highlight_id": highlight.get('id') # Useful for preventing duplicates if needed
                    })
        logging.info(f"Found {len(definitions)} dictionary definitions.")
        return definitions