import sqlite3
from datetime import datetime, timedelta, date

DB_NAME = "wordle.db"

def initialize_db():
    """Create the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Wordle. Added hard_mode column and made skill/luck nullable
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wordle_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            display_name TEXT,
            game_number TEXT,
            attempts INTEGER,
            skill INTEGER NULL,
            luck INTEGER NULL,
            hard_mode BOOLEAN,
            total_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Connections table (corrected)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            display_name TEXT,
            puzzle_number TEXT,
            total_score INTEGER,
            guesses INTEGER,
            solved_purple_first BOOLEAN,
            solved_blue_first BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Generic table for tracking latest game numbers/dates - CHANGE latest_number to TEXT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS latest_game_numbers (
            game_name TEXT PRIMARY KEY,
            latest_number TEXT -- Changed from INTEGER to TEXT
        )
    """)
    conn.commit() # Commit schema change before inserting data

    # Initialize latest numbers if not present - use string '0' or default date
    initial_games = [
        ('Wordle', '0'),
        ('Connections', '0'),
        ('Gisnep', '0'),
        ('Bandle', '0'),
        ('Minute Cryptic', '2000-01-01') # Use an old ISO date string as default
    ]
    # Use INSERT OR IGNORE to safely add initial values without overwriting existing ones
    try:
        cursor.executemany("INSERT OR IGNORE INTO latest_game_numbers (game_name, latest_number) VALUES (?, ?)", initial_games)
    except sqlite3.IntegrityError:
        print("DB: Initial game numbers likely already exist.") # Handle potential race condition or re-run
    except sqlite3.Error as e:
        print(f"Database error during initial game number insertion: {e}")

    conn.commit()
    conn.close()
    print("Database initialized successfully (latest_number is TEXT).")

    # Framed Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS framed_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            display_name TEXT,
            game_number INTEGER,
            attempts INTEGER,
            total_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Gisnep Table (Stores time instead of points)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gisnep_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            display_name TEXT,
            game_number INTEGER,
            completion_time INTEGER, -- Time in seconds
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bandle Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bandle_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            display_name TEXT,
            game_number INTEGER,
            attempts INTEGER,
            total_score INTEGER,
            bonus_completed INTEGER,
            bonus_total INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

        # New table for Minute Cryptic
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS minute_cryptic_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            display_name TEXT,
            game_date TEXT, -- Store as ISO format string 'YYYY-MM-DD'
            clue TEXT,
            word_length INTEGER,
            grid TEXT,
            score_description TEXT,
            score_value INTEGER, -- Numerical score (0=solved, >0 = over par, -1=unknown)
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def save_wordle_score(user_id, display_name, game_number, attempts, skill=None, luck=None, hard_mode=False):
    """Save a new Wordle score with optional skill, luck, and hard mode flag."""
    if attempts == 1:
        attempt_score = 100
    elif attempts == 2:
        attempt_score = 80
    elif attempts == 3:
        attempt_score = 60
    elif attempts == 4:
        attempt_score = 40
    elif attempts == 5:
        attempt_score = 20
    else:
        attempt_score = 0

    total_score = (skill or 0) + attempt_score - (luck or 0)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO wordle_scores (user_id, display_name, game_number, attempts, skill, luck, hard_mode, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, display_name, game_number, attempts, skill, luck, hard_mode, total_score))
    conn.commit()
    conn.close()
    
def get_recent_scores(user_id, limit=5):
    """Retrieve the last `limit` games played by a user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT game_number, attempts, skill, luck, timestamp
        FROM wordle_scores
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def save_connections_score(user_id, display_name, puzzle_number, total_score, guesses, solved_purple_first, solved_blue_first):
    """Save a new Connections score."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO connections_scores (user_id, display_name, puzzle_number, total_score, guesses, solved_purple_first, solved_blue_first)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, display_name, puzzle_number, total_score, guesses, solved_purple_first, solved_blue_first))
    conn.commit()
    conn.close()

def create_connections_scores_table():
    """Create the Connections scores table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections_scores (
            user_id INTEGER,
            display_name TEXT,
            puzzle_number INTEGER,
            total_score INTEGER,
            guesses INTEGER,
            solved_purple_first BOOLEAN,
            solved_blue_first BOOLEAN,
            PRIMARY KEY (user_id, puzzle_number)
        )
    """)
    conn.commit()
    conn.close()

def save_framed_score(user_id, display_name, game_number, attempts, total_score):
    """Save a new Framed score."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO framed_scores (user_id, display_name, game_number, attempts, total_score)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, display_name, game_number, attempts, total_score))
    conn.commit()
    conn.close()

def save_gisnep_score(user_id, display_name, game_number, completion_time):
    """Save a new Gisnep score (only stores time)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO gisnep_scores (user_id, display_name, game_number, completion_time)
        VALUES (?, ?, ?, ?)
    """, (user_id, display_name, game_number, completion_time))
    conn.commit()
    conn.close()

def save_bandle_score(user_id, display_name, game_number, attempts, total_score, bonus_completed, bonus_total):
    """Save a new Bandle score, including bonus rounds separately."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bandle_scores (user_id, display_name, game_number, attempts, total_score, bonus_completed, bonus_total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, display_name, game_number, attempts, total_score, bonus_completed, bonus_total))
    conn.commit()
    conn.close()

def save_minute_cryptic_score(user_id: int, display_name: str, game_info: dict[str, any]):
    """Saves a Minute Cryptic score to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO minute_cryptic_scores (
                user_id, display_name, game_date, clue, word_length,
                grid, score_description, score_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            display_name,
            game_info.get("game_date"),
            game_info.get("clue"),
            game_info.get("word_length"),
            game_info.get("grid"),
            game_info.get("score_description"),
            game_info.get("score_value")
        ))
        conn.commit()
        print(f"DB: Saved Minute Cryptic score for {display_name} on {game_info.get('game_date')}")
    except sqlite3.Error as e:
        print(f"Database error in save_minute_cryptic_score: {e}")
    finally:
        conn.close()

def get_wordle_leaderboard():
    """Fetch the top players for Wordle leaderboard."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT display_name, MAX(total_score) AS best_score
        FROM wordle_scores
        GROUP BY display_name
        ORDER BY best_score DESC
        LIMIT 10
    """)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def get_connections_leaderboard():
    """Fetch the top players for Connections leaderboard."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT display_name, SUM(total_score) AS total_score
        FROM connections_scores
        GROUP BY display_name
        ORDER BY total_score DESC
        LIMIT 10
    """)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def get_framed_leaderboard():
    """Fetch top players for Framed based on highest scores."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT display_name, MAX(total_score) AS best_score
        FROM framed_scores
        GROUP BY display_name
        ORDER BY best_score DESC
        LIMIT 10
    """)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def get_gisnep_leaderboard():
    """Fetch top players for Gisnep, ranking by shortest average time."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT display_name, AVG(completion_time) AS avg_time, COUNT(*) AS games_played
        FROM gisnep_scores
        GROUP BY display_name
        ORDER BY avg_time ASC, games_played DESC
        LIMIT 10
    """)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def get_bandle_leaderboard():
    """Fetch top players for Bandle based on highest total scores."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT display_name, SUM(total_score) AS total_score
        FROM bandle_scores
        GROUP BY display_name
        ORDER BY total_score DESC
        LIMIT 10
    """)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def get_minute_cryptic_leaderboard(period: str = 'weekly') -> list[tuple[str, int]]:
    """
    Fetches the Minute Cryptic leaderboard data.
    Currently counts number of puzzles solved (score_value = 0) in the given period.
    'weekly' = last 7 days, 'monthly' = last 30 days.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    leaderboard = []

    if period == 'weekly':
        days = 7
    elif period == 'monthly':
        days = 30
    else: # Default to weekly if period is invalid
        days = 7

    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Query counts puzzles solved (score_value = 0) within the time period
        cursor.execute("""
            SELECT display_name, COUNT(id) as solved_count
            FROM minute_cryptic_scores
            WHERE score_value = 0 AND timestamp >= ?
            GROUP BY user_id, display_name
            ORDER BY solved_count DESC
            LIMIT 10
        """, (start_date,))
        leaderboard = cursor.fetchall()
        print(f"DB: Fetched Minute Cryptic {period} leaderboard ({len(leaderboard)} players).")
    except sqlite3.Error as e:
        print(f"Database error in get_minute_cryptic_leaderboard: {e}")
    finally:
        conn.close()

    # Return list of (display_name, solved_count)
    return leaderboard

def get_weekly_scores():
    """Fetch total scores for all games for the past week."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    one_week_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Wordle
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM wordle_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (one_week_ago,))
        wordle_scores = cursor.fetchall()

        # Connections
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM connections_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (one_week_ago,))
        connections_scores = cursor.fetchall()

        # Framed
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM framed_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (one_week_ago,))
        framed_scores = cursor.fetchall()

        # Gisnep (rank by shortest average time)
        cursor.execute("""
            SELECT display_name, AVG(completion_time) AS avg_time
            FROM gisnep_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY avg_time ASC
        """, (one_week_ago,))
        gisnep_scores = cursor.fetchall()

        # Bandle
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM bandle_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (one_week_ago,))
        bandle_scores = cursor.fetchall()

        conn.close()

        return {
            "Wordle": wordle_scores,
            "Connections": connections_scores,
            "Framed": framed_scores,
            "Gisnep": gisnep_scores,
            "Bandle": bandle_scores
        }

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.close()
        return {}

def get_monthly_scores():
    """Fetch total scores for all games for the past month."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Wordle
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM wordle_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (first_day_of_month,))
        wordle_scores = cursor.fetchall()

        # Connections
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM connections_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (first_day_of_month,))
        connections_scores = cursor.fetchall()

        # Framed
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM framed_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (first_day_of_month,))
        framed_scores = cursor.fetchall()

        # Gisnep (rank by shortest average time)
        cursor.execute("""
            SELECT display_name, AVG(completion_time) AS avg_time
            FROM gisnep_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY avg_time ASC
        """, (first_day_of_month,))
        gisnep_scores = cursor.fetchall()

        # Bandle
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM bandle_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (first_day_of_month,))
        bandle_scores = cursor.fetchall()

        conn.close()

        return {
            "Wordle": wordle_scores,
            "Connections": connections_scores,
            "Framed": framed_scores,
            "Gisnep": gisnep_scores,
            "Bandle": bandle_scores
        }

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.close()
        return {}

# Database functions for tracking roles (add these to your database.py file)
def save_user_role(user_id, role_name, game_number, expires_at):
    """Save information about a role granted to a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_roles 
        (user_id, role_name, game_number, expires_at) 
        VALUES (?, ?, ?, ?)
    ''', (user_id, role_name, game_number, expires_at))
    conn.commit()
    conn.close()

def get_expired_roles():
    """Get all expired roles that need to be removed."""
    now = datetime.datetime.now(cet_timezone).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, role_name FROM user_roles
        WHERE expires_at < ?
    ''', (now,))
    expired_roles = cursor.fetchall()
    conn.close()
    return expired_roles

def delete_expired_roles():
    """Delete records of expired roles from the database."""
    now = datetime.datetime.now(cet_timezone).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM user_roles WHERE expires_at < ?
    ''', (now,))
    conn.commit()
    conn.close()

def get_overall_recent_wordle_scores(limit=5):
    """
    Fetches the most recent Wordle scores from all users, ordered by timestamp descending,
    limited to the specified number.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT game_number, attempts, skill, luck, timestamp
            FROM wordle_scores
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        scores = cursor.fetchall()
        return scores
    except sqlite3.Error as e:
        print(f"Database error in get_overall_recent_wordle_scores: {e}")
        return [] # Return empty list in case of error
    finally:
        conn.close()

def get_overall_recent_connections_puzzle_number(limit=5):
    """
    Fetches the most recent Connections puzzle numbers from all users,
    ordered by timestamp descending, limited to the specified number.
    Returns a list of tuples, each containing (puzzle_number, timestamp).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT puzzle_number, timestamp
            FROM connections_scores
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        puzzles = cursor.fetchall()
        return puzzles
    except sqlite3.Error as e:
        print(f"Database error in get_overall_recent_connections_puzzle_number: {e}")
        return [] # Return empty list in case of error
    finally:
        conn.close()
        
def get_latest_game_number_from_db(game_name: str) -> str:
    """Fetches the latest game identifier (number or date string) from the database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Easier access by column name
    cursor = conn.cursor()
    latest_identifier = None
    try:
        cursor.execute("SELECT latest_number FROM latest_game_numbers WHERE game_name = ?", (game_name,))
        result = cursor.fetchone()
        if result:
            latest_identifier = result['latest_number']
            print(f"DB: Retrieved latest_identifier for {game_name} = {latest_identifier}")
        else:
            # Fallback if game somehow isn't in the table (shouldn't happen after init)
            print(f"DB WARNING: Game '{game_name}' not found in latest_game_numbers. Returning default.")
            if game_name == 'Minute Cryptic':
                latest_identifier = '2000-01-01'
            else:
                latest_identifier = '0'
    except sqlite3.Error as e:
        print(f"Database error in get_latest_game_number_from_db for {game_name}: {e}")
        # Fallback on error
        if game_name == 'Minute Cryptic':
             latest_identifier = '2000-01-01'
        else:
             latest_identifier = '0'
    finally:
        conn.close()

    return latest_identifier

def update_latest_game_number_in_db(game_name: str, latest_identifier: str):
    """Updates the latest game identifier (number or date string) in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO latest_game_numbers (game_name, latest_number) VALUES (?, ?)",
                       (game_name, str(latest_identifier))) # Ensure it's stored as string
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_latest_game_number_in_db for {game_name}: {e}")
    finally:
        conn.close()
