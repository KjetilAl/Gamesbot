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

Roadmap
==================================================

1. Expand and refine weekly and monthly posts
2. Clean up bot messages (acknowledgements and introductions)
3. Parse Bandle bonus scores in a better way (individually)
4. New games?
5. Invite people
