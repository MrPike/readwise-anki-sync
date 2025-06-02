# Readwise to Anki Dictionary Sync

This script connects to the Readwise API, fetches new highlights, identifies dictionary definitions (e.g., "word (type): definition"), and adds them as new notes to a specified Anki deck using AnkiConnect. It's designed to be run periodically, for example, every hour via a scheduler like `launchd` on macOS.

## Features

* Fetches new highlights from Readwise since the last run.
* Parses highlights to find dictionary definitions based on the format: `word (type): definition`.
* Checks if Anki is running and attempts to launch it if not (macOS only).
* Ensures the specified Anki deck exists, creating it if necessary.
* Adds new definitions to Anki, with basic duplicate avoidance.
* Stores the timestamp of the last successful run to avoid processing old highlights repeatedly.
* Configuration via a `.env` file.

## Prerequisites

* **Python 3.8+**
* **`uv`**: The Python packaging tool. (Installation: `pip install uv` or see [official `uv` documentation](https://github.com/astral-sh/uv))
* **Anki**: The desktop application must be installed.
* **AnkiConnect Add-on**: This Anki add-on must be installed and configured in Anki. You can get it by going to Tools > Add-ons in Anki, then "Get Add-ons..." and pasting the code `2055492159`.

## Installation

1.  **Download Files:**
    Ensure you have all the script files (`main.py`, `readwise_client.py`, `anki_client.py`, `utils.py`) in a dedicated directory (e.g., `readwise-anki-sync`). You will also need to define your dependencies, which are `requests` and `python-dotenv`.

2.  **Navigate to Project Directory:**
    Open your terminal and change to the directory where you saved the files:
    ```bash
    cd path/to/readwise-anki-sync
    ```

3.  **Initialize Project and Install Dependencies:**
    This setup uses `uv` to manage the project environment and dependencies.
    ```bash
    uv init
    ```
    This command will guide you through creating a `pyproject.toml` file, which will define your project's metadata and dependencies. When prompted, or by editing the `pyproject.toml` file afterwards, ensure your project dependencies are listed. For this project, you need `requests` and `python-dotenv`. Your `[project.dependencies]` section in `pyproject.toml` should look something like this:
    ```toml
    [project.dependencies]
    requests = "*"  # Or a more specific version like "requests >=2.20"
    python-dotenv = "*" # Or a more specific version like "python-dotenv >=0.20"
    ```
    If you have a `requirements.txt` file, `uv init` might offer to migrate dependencies from it.

    Once `pyproject.toml` is configured with the dependencies, run:
    ```bash
    uv sync
    ```
    This command will create a virtual environment (typically named `.venv` in your project directory) if one doesn't already exist, and then install all the dependencies specified in your `pyproject.toml` into that environment.

## Configuration

1.  **Create `.env` File:**
    In the project directory (`readwise-anki-sync`), create a file named `.env`.

2.  **Add Configuration Variables:**
    Open the `.env` file with a text editor and add the following lines, replacing the placeholder values with your actual information:

    ```env
    # .env
    READWISE_API_TOKEN="YOUR_READWISE_ACCESS_TOKEN"
    ANKI_DECK_NAME="Vocabulary" # Or your preferred Anki deck name for definitions
    ANKI_MODEL_NAME="Basic"     # The Anki note type (e.g., "Basic", "Basic (and reversed card)")
    ANKI_CONNECT_URL="[http://127.0.0.1:8765](http://127.0.0.1:8765)" # Default AnkiConnect URL
    ANKI_APP_PATH="/Applications/Anki.app" # Path to your Anki application (macOS example)
    # For Windows, an example path might be:
    # ANKI_APP_PATH="C:\Program Files\Anki\anki.exe"
    ```

    * `READWISE_API_TOKEN`: Your personal Readwise access token. Get it from [readwise.io/access_token](https://readwise.io/access_token).
    * `ANKI_DECK_NAME`: The name of the Anki deck where new vocabulary notes will be added.
    * `ANKI_MODEL_NAME`: The Anki Note Type to use (e.g., "Basic"). Ensure this model exists in Anki and has fields like "Front" and "Back".
    * `ANKI_CONNECT_URL`: The URL AnkiConnect listens on. Default is usually fine.
    * `ANKI_APP_PATH`: The full path to your Anki application executable. This is used by the script to try and open Anki if it's not running.

## Running the Script

1.  **Ensure Anki is Running:** For the script to add notes, Anki must be open with AnkiConnect active. The script will attempt to launch Anki if it's not detected, but it's best to have it open.

2.  **Run Manually:**
    From your project directory (`readwise-anki-sync`), you can run the script using `uv run`:
    ```bash
    uv run main.py
    ```uv` will automatically use the project's virtual environment (created by `uv sync`) to run the script. You do not need to manually activate the virtual environment (e.g., `source .venv/bin/activate`).

    You should see log output in the terminal indicating the script's progress.

## Scheduling (Example for macOS with `launchd`)

To run the script automatically (e.g., every hour) on macOS, you can use `launchd`. This example uses `uv run` which simplifies environment management.

1.  **Create a `.plist` file:**
    Create a file named `com.user.readwiseankisync.plist` (or similar) in `~/Library/LaunchAgents/`.

2.  **Edit the `.plist` file:**
    Add the following content. **Crucially, replace `/path/to/your/uv_executable` with the absolute path to your `uv` executable.** Also, ensure the `WorkingDirectory` is correct.

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "[http://www.apple.com/DTDs/PropertyList-1.0.dtd](http://www.apple.com/DTDs/PropertyList-1.0.dtd)">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.user.readwiseankisync</string>

        <key>ProgramArguments</key>
        <array>
            <string>/path/to/your/uv_executable</string>
            <string>run</string>
            <string>main.py</string>
        </array>

        <key>WorkingDirectory</key>
        <string>/Users/yourusername/path/to/readwise-anki-sync</string>

        <key>StartInterval</key>
        <integer>3600</integer>
        <key>RunAtLoad</key>
        <true/>
        <key>StandardOutPath</key>
        <string>/tmp/readwiseankisync.out.log</string>
        <key>StandardErrorPath</key>
        <string>/tmp/readwiseankisync.err.log</string>
    </dict>
    </plist>
    ```
    * **Finding `uv` path**: If you installed `uv` globally (e.g., via `pipx` or `brew`), you can find its path by running `which uv` in your terminal. If it's installed in a specific Python environment's `bin` directory and you want to use that specific `uv`, provide that path.
    * The `WorkingDirectory` must be set to your project directory so `uv run` can find `main.py` and the associated Python environment (managed via `pyproject.toml` and the `.venv` folder).

3.  **Load the `launchd` agent:**
    ```bash
    launchctl load ~/Library/LaunchAgents/com.user.readwiseankisync.plist
    ```
    To start it immediately for testing:
    ```bash
    launchctl start com.user.readwiseankisync
    ```

## Important Notes

* **Definition Format:** The script looks for highlights where the **note field** (not the highlighted text itself) is in the format: `word (type): definition`. For example: `serendipity (noun): the occurrence and development of events by chance in a happy or beneficial way.`
* **AnkiConnect:** Anki must be running, and the AnkiConnect add-on must be enabled and working for the script to interact with your Anki collection.
* **First Run:** The first time you run the script, it might try to fetch all your Readwise highlights if a `.last_run` file doesn't exist. Subsequent runs will only fetch highlights updated since the last successful run.

## Troubleshooting

* **Permission Errors:** Ensure the script has write permissions in its directory to create/update the `.last_run` file. If using `launchd`, check the permissions of the log file paths if specified.
* **"Could not connect to AnkiConnect"**:
    * Verify Anki is running.
    * Verify the AnkiConnect add-on is installed and enabled in Anki.
    * Check that AnkiConnect is listening on the URL specified in `.env` (usually `http://127.0.0.1:8765`). You can check this in AnkiConnect's settings in Anki's add-on manager.
* **Invalid Readwise Token**: Double-check your `READWISE_API_TOKEN` in the `.env` file.
* **Path for `launchd`**: Ensure the path to your `uv` executable and the `WorkingDirectory` in your `.plist` file are correct. `uv run` needs to be able to find `main.py` within the `WorkingDirectory` and resolve the correct Python environment.
