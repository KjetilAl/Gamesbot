Running Tests
==================================================

Commands to install dependencies and run unit tests (bash syntax).

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install required packages
pip3 install -r requirements.txt

# Run unit tests
python3 -m unittest

# Run unit tests with log level DEBUG
LOG_LEVEL=DEBUG python3 -m unittest

# Exit virtual environment
deactivate
```

## Example Scores Spreadsheet

The unit tests test the score parser against hand-parsed example scores
in a spreadsheet.
There is [a collaborative version of the spreadsheet on Google Drive](https://docs.google.com/spreadsheets/d/1hEqFFzgjQrj5TBNalnmL_RpdjUQbmSyvnmZ_ZTRb3nA/edit?usp=sharing),
and there are twin local copies:

* 'Minigame Scores Examples.fods':
    A copy of the file in plain-text XML that is easier for Git to work with.
    This is the copy that is actually stored in Git.

* 'Minigame Scores Examples.ods':
    A local copy in standard compressed OpenDocument format.
    This can be downloaded from Google Drive or created from the `.fods`.

* If one of these files is changed
    (e.g. if you check out a newer flat `.fods` from Git
     or download a new `.ods` from Google Drive),
    then the next time you run the unit tests,
    a setup routine will update the older file to match the newer file.

To add examples, update the shared Google Docs spreadsheet,
then download it in OpenDocument format
(File -> Download -> OpenDocument)
and overwrite the '.ods' file.
The next time you run the unit tests, they will update the flat `.fods`
to match the downloaded file.

Roadmap
==================================================

1. Expand and refine weekly and monthly posts
2. Clean up bot messages (acknowledgements and introductions)
3. Parse Bandle bonus scores in a better way (individually)
4. New games?
5. Invite people


# update_database_manually.py
import sqlite3
import sys # Import sys for exiting on error

DB_NAME = "wordle.db"

def run_manual_update():
    """
    Manually updates the database schema and data.
    - Creates minute_cryptic_scores table if needed.
    - Changes latest_game_numbers.latest_number column type to TEXT.
    - Inserts initial data for Minute Cryptic.
    """
    conn = None
    try:
        print(f"Connecting to database: {DB_NAME}")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print("Connection successful.")

        # --- Step 1: Add the minute_cryptic_scores table (if it doesn't exist) ---
        print("Ensuring minute_cryptic_scores table exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS minute_cryptic_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_date TEXT, clue TEXT, word_length INTEGER, grid TEXT,
                score_description TEXT, score_value INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("minute_cryptic_scores table checked/created.")

        # --- Step 2: Change the latest_number column type in latest_game_numbers ---
        # Using executescript for the multi-step ALTER TABLE process
        print("Altering latest_game_numbers table to change latest_number type to TEXT...")
        alter_table_script = """
            PRAGMA foreign_keys=off;

            BEGIN TRANSACTION;

            ALTER TABLE latest_game_numbers RENAME TO temp_latest_game_numbers;

            CREATE TABLE latest_game_numbers (
                game_name TEXT PRIMARY KEY,
                latest_number TEXT -- Correct type
            );

            INSERT INTO latest_game_numbers (game_name, latest_number)
            SELECT game_name, CAST(latest_number AS TEXT)
            FROM temp_latest_game_numbers;

            DROP TABLE temp_latest_game_numbers;

            COMMIT;

            PRAGMA foreign_keys=on;
        """
        # Check if the column type needs changing first (optional but safer)
        cursor.execute("PRAGMA table_info(latest_game_numbers);")
        columns = cursor.fetchall()
        latest_number_col = next((col for col in columns if col[1] == 'latest_number'), None)

        if latest_number_col and latest_number_col[2].upper() != 'TEXT':
            print("Column 'latest_number' is not TEXT. Proceeding with alteration...")
            cursor.executescript(alter_table_script)
            print("latest_game_numbers table altered successfully.")
        elif latest_number_col and latest_number_col[2].upper() == 'TEXT':
             print("Column 'latest_number' is already TEXT. Skipping alteration.")
        else:
             print("Could not verify 'latest_number' column type. Skipping alteration for safety.")


        # --- Step 3: Insert the initial data for Minute Cryptic ---
        print("Inserting initial data for Minute Cryptic...")
        cursor.execute("""
            INSERT OR IGNORE INTO latest_game_numbers (game_name, latest_number)
            VALUES ('Minute Cryptic', '2000-01-01');
        """)
        print("Minute Cryptic initial data inserted or ignored.")

        # --- Commit final changes ---
        conn.commit()
        print("\nDatabase update script finished successfully.")

    except sqlite3.Error as e:
        print(f"\nDATABASE UPDATE FAILED: {e}")
        # Optional: Rollback changes if an error occurred mid-transaction
        if conn:
            print("Rolling back changes...")
            conn.rollback()
        sys.exit(1) # Exit with an error code

    finally:
        # --- Ensure connection is closed ---
        if conn:
            conn.close()
            print("Database connection closed.")

# --- Run the update function when the script is executed ---
if __name__ == "__main__":
    run_manual_update()
