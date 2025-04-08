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
