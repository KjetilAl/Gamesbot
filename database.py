import sqlite3
from datetime import timedelta, date

DB_NAME = "wordle.db"

def initialize_db():
    """Create the database and tables if they don't exist."""
    conn = None # Initialize conn to None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # --- Create All Tables ---
        # Wordle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wordle_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_number TEXT, attempts INTEGER, skill INTEGER NULL, luck INTEGER NULL,
                hard_mode BOOLEAN, total_score INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Connections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                puzzle_number TEXT, total_score INTEGER, guesses INTEGER,
                solved_purple_first BOOLEAN, solved_blue_first BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Minute Cryptic
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS minute_cryptic_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_date TEXT, clue TEXT, word_length INTEGER,
                score_description TEXT, score_value INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Word Salad
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_salad_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_number INTEGER, completion_time_seconds INTEGER, hints_used INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Framed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS framed_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_number INTEGER, attempts INTEGER, total_score INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Gisnep
        cursor.execute("""
             CREATE TABLE IF NOT EXISTS gisnep_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_number INTEGER, completion_time INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
             )
        """)
        # Bandle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bandle_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_number INTEGER, attempts INTEGER, total_score INTEGER,
                bonus_completed INTEGER, bonus_total INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Latest Game Numbers/Identifiers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS latest_game_numbers (
                game_name TEXT PRIMARY KEY,
                latest_number TEXT -- Storing as TEXT for dates/numbers
            )
        """)
        
        # Table for tracking user roles if needed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER,
                role_name TEXT,
                game_number TEXT,
                expires_at TEXT,
                PRIMARY KEY (user_id, role_name)
            )
        """)
        
        # Commit all schema changes together
        conn.commit()
        print("DB: All tables created or verified.")
        
        # --- Initialize latest_game_numbers Data ---
        initial_games = [
            ('Wordle', '0'), ('Connections', '0'), ('Framed', '0'),
            ('Gisnep', '0'), ('Bandle', '0'), ('Minute Cryptic', '2000-01-01')
        ]
        try:
            cursor.executemany("INSERT OR IGNORE INTO latest_game_numbers (game_name, latest_number) VALUES (?, ?)", initial_games)
            # Commit data insertion
            conn.commit()
            print("DB: Initial latest game numbers inserted or verified.")
        except sqlite3.Error as e:
            print(f"Database error during initial game number insertion: {e}")
            
        print("Database initialized successfully.")
        
    except sqlite3.Error as e:
        # This block catches errors from anywhere within the 'try' block above
        print(f"DATABASE INITIALIZATION FAILED: {e}")
        # Optional: Rollback changes if an error occurred mid-transaction
        # if conn:
        #     conn.rollback()
    finally:
        # --- This 'finally' block ensures the connection is closed ---
        # It runs whether the 'try' block succeeded or an 'except' block was triggered.
        if conn:
            conn.close() # This is where the database connection is closed
            print("DB: Connection closed.")

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

def save_bandle_score(user_id, display_name, game_number, attempts, total_score, bonus_completed, bonus_total, bonus_categories: dict[str, bool]):
    """Save a new Bandle score, including individual bonus round results."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO bandle_scores (
                user_id, display_name, game_number, attempts, total_score,
                bonus_completed, bonus_total,
                bonus_microphone, bonus_frame, bonus_person, bonus_globe, bonus_puzzle,
                bonus_calendar, bonus_cd, bonus_timer, bonus_guitar
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, display_name, game_number, attempts, total_score,
            bonus_completed, bonus_total,
            bonus_categories.get("🎤", False), # Get status for each emoji
            bonus_categories.get("🖼️", False),
            bonus_categories.get("🧑", False),
            bonus_categories.get("🌍", False),
            bonus_categories.get("🧩", False),
            bonus_categories.get("📅", False),
            bonus_categories.get("💿", False),
            bonus_categories.get("⏱️", False),
            bonus_categories.get("🎸", False),
        ))
        conn.commit()
        print(f"DB: Saved Bandle score for {display_name} - Game #{game_number}")
    except sqlite3.Error as e:
        print(f"Database error in save_bandle_score: {e}")
    finally:
        conn.close()
        
def save_minute_cryptic_score(user_id: int, display_name: str, game_date: str, clue: str, word_length: int, score_description: str):
    """Saves a Minute Cryptic score to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO minute_cryptic_scores (
                user_id, display_name, game_date, clue, word_length,
                score_description
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            display_name,
            game_date,
            clue,
            word_length,
            score_description
        ))
        conn.commit()
        print(f"DB: Saved Minute Cryptic score for {display_name} on {game_date}")
    except sqlite3.Error as e:
        print(f"Database error in save_minute_cryptic_score: {e}")
    finally:
        conn.close()

def save_word_salad_score(user_id: int, display_name: str, puzzle_number: int,
                         completion_time_seconds: int, hints_used: int, score: int): # <--- Make sure 'score: int' is here!
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Check if a score for this user and puzzle already exists
    cursor.execute("""
        SELECT 1 FROM word_salad_scores
        WHERE user_id = ? AND puzzle_number = ?
    """, (user_id, puzzle_number))
    existing_score = cursor.fetchone()

    if existing_score:
        # Update all fields, including the new 'score'
        cursor.execute("""
            UPDATE word_salad_scores
            SET display_name = ?, completion_time_seconds = ?, hints_used = ?, score = ?, timestamp = ?
            WHERE user_id = ? AND puzzle_number = ?
        """, (display_name, completion_time_seconds, hints_used, score, timestamp, # <--- Ensure 'score' is in this tuple
              user_id, puzzle_number))
        print(f"Updated Word Salad score for {display_name} (Puzzle #{puzzle_number}).")
    else:
        cursor.execute("""
            INSERT INTO word_salad_scores
            (user_id, display_name, puzzle_number, completion_time_seconds, hints_used, score, timestamp) # <--- Ensure 'score' column is listed here
            VALUES (?, ?, ?, ?, ?, ?, ?) # <--- Ensure there's a '?' for the score here
        """, (user_id, display_name, puzzle_number, completion_time_seconds, hints_used, score, timestamp)) # <--- Ensure 'score' value is here
        print(f"Added Word Salad score for {display_name} (Puzzle #{puzzle_number}).")

    conn.commit()
    conn.close()

def get_scores_by_period(table_name: str, period: str) -> tuple[str, ...]:
    """Helper function to get the WHERE clause and parameters for a given period."""
    if period == 'weekly':
        start_time = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        return "WHERE timestamp >= ?", (start_time,)
    elif period == 'monthly':
        first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        return "WHERE timestamp >= ?", (first_day_of_month,)
    else: # overall
        return "", ()

def get_wordle_leaderboard(period: str = 'overall'):
    """Fetch Wordle leaderboard data, supporting different periods and stats."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period("wordle_scores", period)

    # Fetch relevant stats for Wordle
    cursor.execute(f"""
        SELECT display_name,
               COUNT(*) AS games_played,
               AVG(attempts) AS avg_attempts,
               SUM(CASE WHEN attempts <= 6 THEN 1 ELSE 0 END) AS solved_count,
               SUM(CASE WHEN hard_mode THEN 1 ELSE 0 END) AS hard_mode_count,
               MAX(total_score) AS best_score -- Still useful for overall ranking or context
        FROM wordle_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY best_score DESC -- Or order by avg_attempts ASC for weekly/monthly?
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard # Returns list of tuples

def get_connections_leaderboard(period: str = 'overall'):
    """Fetch Connections leaderboard data, supporting different periods and stats."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period("connections_scores", period)

    # Fetch relevant stats for Connections
    cursor.execute(f"""
        SELECT display_name,
               COUNT(*) AS games_played,
               SUM(total_score) AS total_score,
               AVG(total_score) AS avg_score,
               COUNT(*) AS solved_count,
               SUM(CASE WHEN solved_purple_first THEN 1 ELSE 0 END) AS purple_first_count,
               SUM(CASE WHEN solved_blue_first THEN 1 ELSE 0 END) AS blue_first_count
        FROM connections_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY total_score DESC
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard # Returns list of tuples

def get_framed_leaderboard(period: str = 'overall'):
    """Fetch Framed leaderboard data, supporting different periods and stats."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period("framed_scores", period)

    # Fetch relevant stats for Framed
    cursor.execute(f"""
        SELECT display_name,
               COUNT(*) AS games_played,
               SUM(total_score) AS total_score,
               AVG(attempts) AS avg_attempts,
               SUM(CASE WHEN attempts <= 6 THEN 1 ELSE 0 END) AS solved_count -- Assuming attempts <= 6 means solved
        FROM framed_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY total_score DESC
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard # Returns list of tuples

def get_gisnep_leaderboard(period: str = 'overall'):
    """Fetch Gisnep leaderboard data, supporting different periods and stats."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period("gisnep_scores", period)

    # Fetch relevant stats for Gisnep
    cursor.execute(f"""
        SELECT display_name,
               COUNT(*) AS games_played,
               AVG(completion_time) AS avg_time,
               MIN(completion_time) AS best_time
        FROM gisnep_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY avg_time ASC, games_played DESC -- Rank by average time, then games played
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard # Returns list of tuples

def get_bandle_leaderboard(period: str = 'overall'):
    """Fetch Bandle leaderboard data, supporting different periods and stats."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period("bandle_scores", period)

    # Fetch relevant stats for Bandle, including individual bonus counts
    cursor.execute(f"""
        SELECT display_name,
               COUNT(*) AS games_played,
               SUM(total_score) AS total_score,
               AVG(attempts) AS avg_attempts,
               SUM(CASE WHEN attempts <= 6 THEN 1 ELSE 0 END) AS solved_count, -- Assuming attempts <= 6 means solved
               SUM(CASE WHEN bonus_microphone THEN 1 ELSE 0 END) AS bonus_microphone_count,
               SUM(CASE WHEN bonus_frame THEN 1 ELSE 0 END) AS bonus_frame_count,
               SUM(CASE WHEN bonus_person THEN 1 ELSE 0 END) AS bonus_person_count,
               SUM(CASE WHEN bonus_globe THEN 1 ELSE 0 END) AS bonus_globe_count,
               SUM(CASE WHEN bonus_puzzle THEN 1 ELSE 0 END) AS bonus_puzzle_count,
               SUM(CASE WHEN bonus_calendar THEN 1 ELSE 0 END) AS bonus_calendar_count,
               SUM(CASE WHEN bonus_cd THEN 1 ELSE 0 END) AS bonus_cd_count,
               SUM(CASE WHEN bonus_timer THEN 1 ELSE 0 END) AS bonus_timer_count,
               SUM(CASE WHEN bonus_guitar THEN 1 ELSE 0 END) AS bonus_guitar_count
        FROM bandle_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY total_score DESC
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard # Returns list of tuples

def get_minute_cryptic_leaderboard(period: str = 'weekly') -> list[tuple[str, int]]:
    """
    Fetches the Minute Cryptic leaderboard data, supporting different periods and stats.
    Currently counts number of puzzles solved (score_value = 0) in the given period.
    Also fetches average score.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period("minute_cryptic_scores", period)

    # Fetch relevant stats for Minute Cryptic
    cursor.execute(f"""
        SELECT display_name,
               COUNT(id) as games_played,
               SUM(CASE WHEN score_value = 0 THEN 1 ELSE 0 END) AS solved_count, -- Count puzzles solved (score_value = 0)
               AVG(score_value) AS avg_score -- Average score value
        FROM minute_cryptic_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY solved_count DESC, avg_score ASC -- Rank by solved count, then average score (lower is better)
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard # Returns list of tuples

def get_word_salad_leaderboard(period: str = 'overall'):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period("word_salad_scores", period)

    cursor.execute(f"""
        SELECT display_name,
               COUNT(*) AS games_played,
               AVG(completion_time_seconds) AS avg_time,  -- Keep for display if needed
               MIN(completion_time_seconds) AS best_time,  -- Keep for display if needed
               AVG(hints_used) AS avg_hints,               -- Keep for display if needed
               SUM(score) AS total_score,                  -- New: Total calculated score
               AVG(score) AS avg_score                     -- New: Average calculated score
        FROM word_salad_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY avg_score DESC, total_score DESC, games_played DESC -- Rank by average score (HIGHER is better), then total score, then games played
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

# Database functions for tracking roles
def save_user_role(user_id, role_name, game_number, expires_at):
    """Save information about a role granted to a user."""
    conn = sqlite3.connect(DB_NAME)
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
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

def get_latest_minute_cryptic_date(game_key: str):
    """Retrieves the latest game_date from minute_cryptic_scores."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    latest_date = None
    try:
        cursor.execute("SELECT MAX(game_date) FROM minute_cryptic_scores")
        result = cursor.fetchone()
        if result and result[0]:
            latest_date = result[0]
    except sqlite3.Error as e:
        print(f"Database error in get_latest_minute_cryptic_date: {e}")
    finally:
        conn.close()
    return latest_date

def update_latest_minute_cryptic_date(game_date: str):
    """Placeholder function - we are managing the latest date directly in the scores table."""
    pass

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
