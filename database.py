import sqlite3
from datetime import datetime, timedelta

DB_NAME = "wordle.db"

def initialize_db():
    """Create the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Wordle table (unchanged)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wordle_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            display_name TEXT,
            game_number TEXT,
            attempts INTEGER,
            skill INTEGER,
            luck INTEGER,
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

    # Add these new tables for tracking latest game numbers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS latest_wordle (
            id INTEGER PRIMARY KEY,
            game_number INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS latest_connections (
            id INTEGER PRIMARY KEY,
            puzzle_number INTEGER
        )
    """)
    
    # Initialize with 0 if empty
    cursor.execute("INSERT OR IGNORE INTO latest_wordle (id, game_number) VALUES (1, 0)")
    cursor.execute("INSERT OR IGNORE INTO latest_connections (id, puzzle_number) VALUES (1, 0)")
    
    conn.commit()
    conn.close()

def save_wordle_score(user_id, display_name, game_number, attempts, skill, luck):
    """Save a new Wordle score with tiered attempt scoring."""

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

    # Ensure skill and luck are not None
    skill = skill if skill is not None else 0
    luck = luck if luck is not None else 0
    
    total_score = skill + attempt_score - luck  # Luck subtracted here

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO wordle_scores (user_id, display_name, game_number, attempts, skill, luck, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, display_name, game_number, attempts, skill, luck, total_score))
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

def get_weekly_summary():
    """Retrieve all players and their total scores for the past week for both Wordle and Connections."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    one_week_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    # Wordle weekly scores
    cursor.execute("""
        SELECT display_name, SUM(total_score) AS total_score
        FROM wordle_scores
        WHERE timestamp >= ?
        GROUP BY display_name
        ORDER BY total_score DESC
    """, (one_week_ago,))
    wordle_scores = cursor.fetchall()

    # Connections weekly scores
    cursor.execute("""
        SELECT display_name, SUM(total_score) AS total_score
        FROM connections_scores
        WHERE timestamp >= ?
        GROUP BY display_name
        ORDER BY total_score DESC
    """, (one_week_ago,))
    connections_scores = cursor.fetchall()

    conn.close()
    return wordle_scores, connections_scores

def get_weekly_scores():
    """Fetch total Wordle and Connections scores for the past week."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT display_name, SUM(total_score) AS total_score
        FROM wordle_scores
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY display_name
        ORDER BY total_score DESC
    """)
    wordle_scores = cursor.fetchall()

    cursor.execute("""
        SELECT display_name, SUM(total_score) AS total_score
        FROM connections_scores
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY display_name
        ORDER BY total_score DESC
    """)
    connections_scores = cursor.fetchall()

    conn.close()
    return wordle_scores, connections_scores

def get_weekly_scores():
    """Fetch total Wordle and Connections scores for the past week."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    one_week_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    try:
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM wordle_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (one_week_ago,))
        wordle_scores = cursor.fetchall()

        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM connections_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (one_week_ago,))
        connections_scores = cursor.fetchall()

        conn.close()
        return wordle_scores, connections_scores
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.close()
        return [], []

def get_monthly_scores():
    """Fetch total Wordle and Connections scores for the past month."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

    try:
        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM wordle_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (first_day_of_month,))
        wordle_scores = cursor.fetchall()

        cursor.execute("""
            SELECT display_name, SUM(total_score) AS total_score
            FROM connections_scores
            WHERE timestamp >= ?
            GROUP BY display_name
            ORDER BY total_score DESC
        """, (first_day_of_month,))
        connections_scores = cursor.fetchall()

        conn.close()
        return wordle_scores, connections_scores
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.close()
        return [], []
        
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
        
def get_latest_game_number_from_db(game_type):
    """Fetches the latest game/puzzle number from the database."""
    conn = sqlite3.connect(DB_NAME)  # Use your existing DB_NAME variable
    cursor = conn.cursor()
    if game_type == "Wordle":
        cursor.execute("SELECT game_number FROM latest_wordle WHERE id = 1")
    else:  # Connections
        cursor.execute("SELECT puzzle_number FROM latest_connections WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0  # Return 0 if no records exist
    
def update_latest_game_number_in_db(game_type, new_game_number):
    """Updates the latest game/puzzle number in the database."""
    conn = sqlite3.connect(DB_NAME)  # Use your existing DB_NAME variable
    cursor = conn.cursor()
    if game_type == "Wordle":
        cursor.execute("UPDATE latest_wordle SET game_number = ? WHERE id = 1", (new_game_number,))
    else:  # Connections
        cursor.execute("UPDATE latest_connections SET puzzle_number = ? WHERE id = 1", (new_game_number,))
    conn.commit()
    conn.close()
