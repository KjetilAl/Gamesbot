import sqlite3
import datetime
from datetime import timedelta, date, timezone # Added timezone

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
                hard_mode BOOLEAN, total_score INTEGER, created_at DATETIME NOT NULL
            )
        """)
        # Player Stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                total_plays INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                win_percentage REAL DEFAULT 0.0,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                avg_skill REAL DEFAULT 0.0,
                avg_luck REAL DEFAULT 0.0,
                connections_total_plays INTEGER DEFAULT 0,
                connections_perfect_games INTEGER DEFAULT 0,
                connections_purple_firsts INTEGER DEFAULT 0,
                connections_avg_mistakes REAL DEFAULT 0.0,
                gisnep_total_plays INTEGER DEFAULT 0,
                gisnep_avg_seconds REAL DEFAULT 0.0,
                gisnep_personal_best_seconds INTEGER, -- Can be NULL
                sexaginta_total_plays INTEGER DEFAULT 0,
                sexaginta_avg_pct REAL DEFAULT 0.0,
                sexaginta_avg_game_score REAL DEFAULT 0.0,
                framed_total_plays INTEGER DEFAULT 0,
                framed_total_wins INTEGER DEFAULT 0,
                framed_current_streak INTEGER DEFAULT 0,
                framed_max_streak INTEGER DEFAULT 0,
                framed_avg_attempts REAL DEFAULT 0.0,
                framed_avg_score REAL DEFAULT 0.0,
                word_salad_total_plays INTEGER DEFAULT 0,
                word_salad_avg_time REAL DEFAULT 0.0,
                word_salad_personal_best_time INTEGER,
                word_salad_avg_hints REAL DEFAULT 0.0,
                word_salad_avg_score REAL DEFAULT 0.0,
                minute_cryptic_total_plays INTEGER DEFAULT 0,
                minute_cryptic_solved INTEGER DEFAULT 0,
                minute_cryptic_avg_score REAL DEFAULT 0.0,
                pips_total_score INTEGER DEFAULT 0,
                pips_total_cookies INTEGER DEFAULT 0
            )
        """)
        # Connections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                display_name TEXT,
                game_number INTEGER NOT NULL,
                total_score INTEGER,
                mistake_count INTEGER,
                perfect_game BOOLEAN,
                solved_purple_first BOOLEAN,
                skill INTEGER,
                uniqueness_text TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """)
        # Minute Cryptic
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS minute_cryptic_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_date TEXT, clue TEXT, word_length INTEGER,
                score_description TEXT, score_value INTEGER,
                created_at DATETIME NOT NULL
            )
        """)
        # Word Salad
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_salad_scores (
                user_id INTEGER NOT NULL,
                display_name TEXT NOT NULL,
                game_number INTEGER NOT NULL,
                completion_time_seconds INTEGER NOT NULL,
                hints_used INTEGER NOT NULL,
                score INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (user_id, game_number)
            )
        """)
        # Framed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS framed_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, display_name TEXT,
                game_number INTEGER, attempts INTEGER, total_score INTEGER,
                created_at DATETIME NOT NULL
            )
        """)
        # Gisnep
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gisnep_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                display_name TEXT,
                game_number INTEGER NOT NULL,
                completion_time INTEGER NOT NULL, -- Stored in seconds
                created_at TIMESTAMP NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gisnep_puzzle_stats (
                game_number INTEGER PRIMARY KEY,
                total_solves INTEGER DEFAULT 0,
                total_seconds INTEGER DEFAULT 0,
                avg_seconds REAL DEFAULT 0.0
            )
        """)
        # Bandle
        cursor.execute("DROP TABLE IF EXISTS bandle_scores")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bandle_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                display_name TEXT,
                game_number INTEGER NOT NULL,
                attempts INTEGER,
                found_total INTEGER,
                found_percentage REAL,
                current_streak INTEGER,
                max_streak INTEGER,
                bonus_rounds_completed INTEGER,
                bonus_rounds_total INTEGER,
                bonus_emojis TEXT,
                total_score INTEGER,
                created_at TIMESTAMP NOT NULL
            );
        """)
        # Latest Game Numbers/Identifiers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS latest_game_numbers (
                game_name TEXT PRIMARY KEY,
                latest_number TEXT -- Storing as TEXT for dates/numbers
            )
        """)

        # Pips
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pips_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                display_name TEXT NOT NULL,
                game_number INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                completion_time INTEGER NOT NULL,
                score INTEGER NOT NULL,
                cookie BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL,
                UNIQUE(user_id, game_number, difficulty)
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sexaginta_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                display_name TEXT,
                game_number INTEGER NOT NULL,
                guesses_used TEXT,
                guesses_allowed INTEGER,
                percent_solved REAL,
                game_score REAL,
                grid_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("DB: All tables created or verified.")

        migrations = {}
        for table, old_column in migrations.items():
            if old_column:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN created_at TIMESTAMP;")
                    conn.commit()
                    print(f"DB: Added created_at column to {table}.")
                    cursor.execute(f"UPDATE {table} SET created_at = {old_column} WHERE created_at IS NULL;")
                    conn.commit()
                    print(f"DB: Backfilled created_at values in {table} from {old_column}.")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"DB: created_at column already exists in {table}.")
                    else:
                        raise e

        # --- Initialize latest_game_numbers Data ---
        initial_games = [
            ('Wordle', '0'), ('Connections', '0'), ('Framed', '0'),
            ('Gisnep', '0'), ('Bandle', '0'), ('Minute Cryptic', '2000-01-01'),
            ('Pips', '0'), ('Sexaginta', '0')
        ]
        try:
            cursor.executemany(
                "INSERT OR IGNORE INTO latest_game_numbers (game_name, latest_number) VALUES (?, ?)",
                initial_games
            )
            conn.commit()
            print("DB: Initial latest game numbers inserted or verified.")
        except sqlite3.Error as e:
            print(f"Database error during initial game number insertion: {e}")

        print("Database initialized successfully.")

    except sqlite3.Error as e:
        print(f"DATABASE INITIALIZATION FAILED: {e}")
    finally:
        if conn:
            conn.close()
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
    created_at = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO wordle_scores (user_id, display_name, game_number, attempts, skill, luck, hard_mode, total_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, display_name, game_number, attempts, skill, luck, hard_mode, total_score, created_at))
    conn.commit()
    conn.close()

def save_sexaginta_score(user_id, display_name, game_info):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sexaginta_scores
        (user_id, display_name, game_number, percent_solved, game_score, created_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        str(user_id),
        display_name,
        game_info.get("game_number"),
        game_info.get("performance_pct"),
        game_info.get("game_score")
    ))
    conn.commit()
    conn.close()

def update_player_stats(user_id, display_name, game_number, attempts, skill, luck):
    """Update player stats after a new score is submitted."""
    # Use 0 if skill or luck is None
    skill = skill or 0
    luck = luck or 0

    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get the player's current stats
    cursor.execute("""
        SELECT display_name, total_plays, total_wins, current_streak, max_streak, avg_skill, avg_luck
        FROM player_stats
        WHERE user_id = ?
    """, (str(user_id),))
    stats = cursor.fetchone()

    # If player is new, initialize their stats
    if not stats:
        cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (str(user_id), display_name))
        conn.commit()  # Commit the insert
        # Set stats to a default tuple for a new player
        stats = (display_name, 0, 0, 0, 0, 0.0, 0.0)

    # Unpack stats for easier use
    (name, total_plays, total_wins, current_streak, max_streak, avg_skill, avg_luck) = stats

    # --- Streak Logic ---
    was_a_win = (attempts <= 6)

    # Check if the previous day's game was played and won
    cursor.execute("SELECT attempts FROM wordle_scores WHERE user_id = ? AND game_number = ?", (user_id, int(game_number) - 1))
    previous_game = cursor.fetchone()

    is_on_streak = previous_game and previous_game[0] <= 6

    if was_a_win:
        if is_on_streak:
            new_streak = current_streak + 1
        else:
            new_streak = 1
    else: # It was a loss (X/6) or more than 6 attempts
        new_streak = 0

    # --- Update All Stats ---
    new_total_plays = total_plays + 1
    new_total_wins = total_wins + (1 if was_a_win else 0)
    new_win_percentage = (new_total_wins / new_total_plays) * 100 if new_total_plays > 0 else 0.0
    new_max_streak = max(max_streak, new_streak)

    # Recalculate average skill and luck
    new_avg_skill = ((avg_skill * total_plays) + skill) / new_total_plays if new_total_plays > 0 else float(skill)
    new_avg_luck = ((avg_luck * total_plays) + luck) / new_total_plays if new_total_plays > 0 else float(luck)

    # --- Commit changes to the database ---
    cursor.execute("""
        UPDATE player_stats
        SET display_name = ?, total_plays = ?, total_wins = ?, win_percentage = ?,
            current_streak = ?, max_streak = ?, avg_skill = ?, avg_luck = ?
        WHERE user_id = ?
    """, (display_name, new_total_plays, new_total_wins, new_win_percentage, new_streak, new_max_streak, new_avg_skill, new_avg_luck, str(user_id)))

    conn.commit()
    conn.close()

    # Return the updated stats for use in the Discord post
    return {
        "new_streak": new_streak,
        "max_streak": new_max_streak,
        "win_percentage": new_win_percentage,
        "total_plays": new_total_plays,
        "is_new_max_streak": new_streak > max_streak and new_streak > 1
    }

def update_connections_stats(user_id, display_name, mistake_count, perfect_game, solved_purple_first):
    """Update player stats for Connections after a new score is submitted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get the player's current stats
    cursor.execute("SELECT connections_total_plays, connections_perfect_games, connections_purple_firsts, connections_avg_mistakes FROM player_stats WHERE user_id = ?", (str(user_id),))
    stats = cursor.fetchone()

    # If player is new, initialize their stats
    if not stats:
        cursor.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (str(user_id),))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (str(user_id), display_name))
            conn.commit()

        # Now fetch the stats again
        cursor.execute("SELECT connections_total_plays, connections_perfect_games, connections_purple_firsts, connections_avg_mistakes FROM player_stats WHERE user_id = ?", (str(user_id),))
        stats = cursor.fetchone()

    # Unpack stats
    (total_plays, perfect_games, purple_firsts, avg_mistakes) = stats

    # --- Calculate new stats ---
    new_total_plays = total_plays + 1
    new_perfect_games = perfect_games + (1 if perfect_game else 0)
    new_purple_firsts = purple_firsts + (1 if solved_purple_first else 0)
    # Recalculate average mistakes
    new_avg_mistakes = ((avg_mistakes * total_plays) + mistake_count) / new_total_plays if new_total_plays > 0 else float(mistake_count)

    # --- Commit changes to the database ---
    cursor.execute("""
        UPDATE player_stats
        SET connections_total_plays = ?, connections_perfect_games = ?,
            connections_purple_firsts = ?, connections_avg_mistakes = ?
        WHERE user_id = ?
    """, (new_total_plays, new_perfect_games, new_purple_firsts, new_avg_mistakes, str(user_id)))

    conn.commit()
    conn.close()

    # Return key stats for the Discord post
    return { "total_perfects": new_perfect_games, "total_purples": new_purple_firsts }

def save_pips_score(user_id: int, display_name: str, game_number: int, difficulty: str, completion_time: int, score: int, cookie: bool):
    """Saves or updates a Pips score in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        SELECT id FROM pips_scores
        WHERE user_id = ? AND game_number = ? AND difficulty = ?
    """, (user_id, game_number, difficulty))
    existing_score = cursor.fetchone()

    if existing_score:
        cursor.execute("""
            UPDATE pips_scores
            SET display_name = ?, completion_time = ?, score = ?, cookie = ?, created_at = ?
            WHERE user_id = ? AND game_number = ? AND difficulty = ?
        """, (display_name, completion_time, score, cookie, created_at, user_id, game_number, difficulty))
        print(f"Updated Pips score for {display_name} (Game #{game_number}, {difficulty}).")
    else:
        cursor.execute("""
            INSERT INTO pips_scores
            (user_id, display_name, game_number, difficulty, completion_time, score, cookie, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, display_name, game_number, difficulty, completion_time, score, cookie, created_at))
        print(f"Added Pips score for {display_name} (Game #{game_number}, {difficulty}).")

    conn.commit()
    conn.close()

def get_recent_scores(user_id, limit=5):
    """Retrieve the last `limit` games played by a user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT game_number, attempts, skill, luck, created_at
        FROM wordle_scores
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def save_connections_score(user_id, display_name, game_number, total_score, mistake_count, perfect_game, solved_purple_first, skill, uniqueness_text):
    """Save a new Connections score."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO connections_scores (user_id, display_name, game_number, total_score, mistake_count, perfect_game, solved_purple_first, skill, uniqueness_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (str(user_id), display_name, game_number, total_score, mistake_count, perfect_game, solved_purple_first, skill, uniqueness_text, created_at))
    conn.commit()
    conn.close()

def save_framed_score(user_id, display_name, game_number, attempts, total_score):
    """Save a new Framed score."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO framed_scores (user_id, display_name, game_number, attempts, total_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, display_name, game_number, attempts, total_score, created_at))
    conn.commit()
    conn.close()

def save_gisnep_score(user_id, display_name, game_number, completion_time):
    """Save a new Gisnep score (only stores time)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO gisnep_scores (user_id, display_name, game_number, completion_time, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, display_name, game_number, completion_time, created_at))
    conn.commit()
    conn.close()

def update_gisnep_puzzle_stats(game_number, completion_time):
    """Updates the server-wide stats for a specific Gisnep puzzle."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT total_solves, total_seconds FROM gisnep_puzzle_stats WHERE game_number = ?", (game_number,))
    stats = cursor.fetchone()

    if stats:
        new_total_solves = stats[0] + 1
        new_total_seconds = stats[1] + completion_time
        new_avg_seconds = new_total_seconds / new_total_solves
        cursor.execute("""
            UPDATE gisnep_puzzle_stats
            SET total_solves = ?, total_seconds = ?, avg_seconds = ?
            WHERE game_number = ?
        """, (new_total_solves, new_total_seconds, new_avg_seconds, game_number))
    else:
        cursor.execute("""
            INSERT INTO gisnep_puzzle_stats (game_number, total_solves, total_seconds, avg_seconds)
            VALUES (?, ?, ?, ?)
        """, (game_number, 1, completion_time, float(completion_time)))
    conn.commit()
    conn.close()

def update_gisnep_player_stats(user_id, display_name, completion_time):
    """Updates a player's Gisnep stats and returns the new stats."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Ensure the player exists in the player_stats table
    cursor.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (user_id, display_name))
        conn.commit()

    cursor.execute("""
        SELECT gisnep_total_plays, gisnep_avg_seconds, gisnep_personal_best_seconds
        FROM player_stats WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()

    total_plays, avg_seconds, personal_best = stats

    # Safely handle None values
    total_plays = total_plays or 0
    avg_seconds = avg_seconds or 0.0

    new_total_plays = total_plays + 1
    new_avg_seconds = ((avg_seconds * total_plays) + completion_time) / new_total_plays

    is_new_pb = False
    if personal_best is None or completion_time < personal_best:
        personal_best = completion_time
        is_new_pb = True

    cursor.execute("""
        UPDATE player_stats
        SET gisnep_total_plays = ?, gisnep_avg_seconds = ?, gisnep_personal_best_seconds = ?, display_name = ?
        WHERE user_id = ?
    """, (new_total_plays, new_avg_seconds, personal_best, display_name, user_id))
    conn.commit()
    conn.close()

    return {
        "is_new_pb": is_new_pb,
        "personal_best": personal_best,
        "avg_seconds": new_avg_seconds,
        "total_plays": new_total_plays
    }

def save_bandle_score(user_id, display_name, game_number, attempts, found_total, found_percentage, current_streak, max_streak, bonus_rounds_completed, bonus_rounds_total, bonus_emojis, total_score):
    """Save a new Bandle score."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    try:
        cursor.execute("""
            INSERT INTO bandle_scores (
                user_id, display_name, game_number, attempts, found_total,
                found_percentage, current_streak, max_streak,
                bonus_rounds_completed, bonus_rounds_total, bonus_emojis, total_score,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, display_name, game_number, attempts, found_total,
            found_percentage, current_streak, max_streak,
            bonus_rounds_completed, bonus_rounds_total, bonus_emojis, total_score,
            created_at
        ))
        conn.commit()
        print(f"DB: Saved Bandle score for {display_name} - Game #{game_number}")
    except sqlite3.Error as e:
        print(f"Database error in save_bandle_score: {e}")
    finally:
        conn.close()

def update_bandle_player_stats(user_id, display_name, attempts, bonus_rounds_completed):
    """Update player stats for Bandle after a new score is submitted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT bandle_total_plays, bandle_avg_attempts, bandle_avg_bonus_rounds FROM player_stats WHERE user_id = ?", (str(user_id),))
    stats = cursor.fetchone()

    if not stats or stats[0] is None:
        # If stats are not found or total_plays is NULL, initialize them
        total_plays, avg_attempts, avg_bonus_rounds = 0, 0.0, 0.0
        # Ensure the player exists in the table
        cursor.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (str(user_id),))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (str(user_id), display_name))
    else:
        total_plays, avg_attempts, avg_bonus_rounds = stats

    # --- Calculate new stats ---
    new_total_plays = total_plays + 1
    # Recalculate average attempts
    new_avg_attempts = ((avg_attempts * total_plays) + attempts) / new_total_plays
    # Recalculate average bonus rounds
    new_avg_bonus_rounds = ((avg_bonus_rounds * total_plays) + bonus_rounds_completed) / new_total_plays

    # --- Commit changes to the database ---
    cursor.execute("""
        UPDATE player_stats
        SET display_name = ?,
            bandle_total_plays = ?,
            bandle_avg_attempts = ?,
            bandle_avg_bonus_rounds = ?
        WHERE user_id = ?
    """, (display_name, new_total_plays, new_avg_attempts, new_avg_bonus_rounds, str(user_id)))

    conn.commit()
    conn.close()

    # Return key stats for the post
    return {
        "total_plays": new_total_plays,
        "avg_attempts": new_avg_attempts,
        "avg_bonus_rounds": new_avg_bonus_rounds
    }

def update_sexaginta_stats(user_id, display_name, game_info):
    """Update player stats for Sexaginta-quattuordle after a new score is submitted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT sexaginta_total_plays, sexaginta_avg_pct, sexaginta_avg_game_score FROM player_stats WHERE user_id = ?", (str(user_id),))
    stats = cursor.fetchone()

    if not stats or stats[0] is None:
        # If stats are not found or total_plays is NULL, initialize them
        total_plays, avg_pct, avg_game_score = 0, 0.0, 0.0
        # Ensure the player exists in the table
        cursor.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (str(user_id),))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (str(user_id), display_name))
    else:
        # Unpack the fetched values and ensure they are not None
        total_plays, avg_pct, avg_game_score = stats
        # Explicitly handle potential None values before calculations
        total_plays = total_plays or 0
        avg_pct = avg_pct or 0.0
        avg_game_score = avg_game_score or 0.0

    # Fix: Handle None values from game_info
    performance_pct = game_info.get("performance_pct") or 0
    game_score = game_info.get("game_score") or 0

    new_total_plays = total_plays + 1
    new_avg_pct = ((avg_pct * total_plays) + performance_pct) / new_total_plays
    new_avg_game_score = ((avg_game_score * total_plays) + game_score) / new_total_plays

    cursor.execute("""
        UPDATE player_stats
        SET display_name = ?,
            sexaginta_total_plays = ?,
            sexaginta_avg_pct = ?,
            sexaginta_avg_game_score = ?
        WHERE user_id = ?
    """, (display_name, new_total_plays, new_avg_pct, new_avg_game_score, str(user_id)))

    conn.commit()
    conn.close()

    return {
        "total_plays": new_total_plays,
        "avg_pct": new_avg_pct,
        "avg_game_score": new_avg_game_score
    }

def update_framed_player_stats(user_id, display_name, game_info):
    """Update player stats for Framed after a new score is submitted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT framed_total_plays, framed_total_wins, framed_current_streak, framed_max_streak, framed_avg_attempts, framed_avg_score FROM player_stats WHERE user_id = ?", (str(user_id),))
    stats = cursor.fetchone()

    if not stats or stats[0] is None:
        total_plays, total_wins, current_streak, max_streak, avg_attempts, avg_score = 0, 0, 0, 0, 0.0, 0.0
        cursor.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (str(user_id),))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (str(user_id), display_name))
    else:
        total_plays, total_wins, current_streak, max_streak, avg_attempts, avg_score = stats

    # --- Calculate new stats ---
    new_total_plays = total_plays + 1
    was_a_win = game_info.get("solved", False)
    new_total_wins = total_wins + (1 if was_a_win else 0)

    if was_a_win:
        new_streak = current_streak + 1
    else:
        new_streak = 0

    new_max_streak = max(max_streak, new_streak)

    attempts = game_info.get("attempts", 7)
    new_avg_attempts = ((avg_attempts * total_plays) + attempts) / new_total_plays if new_total_plays > 0 else float(attempts)

    score = game_info.get("total_score", 0)
    new_avg_score = ((avg_score * total_plays) + score) / new_total_plays if new_total_plays > 0 else float(score)

    cursor.execute("""
        UPDATE player_stats
        SET display_name = ?, framed_total_plays = ?, framed_total_wins = ?, framed_current_streak = ?, framed_max_streak = ?, framed_avg_attempts = ?, framed_avg_score = ?
        WHERE user_id = ?
    """, (display_name, new_total_plays, new_total_wins, new_streak, new_max_streak, new_avg_attempts, new_avg_score, str(user_id)))

    conn.commit()
    conn.close()

    return {
        "total_plays": new_total_plays,
        "total_wins": new_total_wins,
        "current_streak": new_streak,
        "max_streak": new_max_streak,
        "is_new_max_streak": new_streak > max_streak and new_streak > 1,
        "avg_attempts": new_avg_attempts,
        "avg_score": new_avg_score
    }

def update_word_salad_player_stats(user_id, display_name, game_info):
    """Update player stats for Word Salad after a new score is submitted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT word_salad_total_plays, word_salad_avg_time, word_salad_personal_best_time, word_salad_avg_hints, word_salad_avg_score FROM player_stats WHERE user_id = ?", (str(user_id),))
    stats = cursor.fetchone()

    if not stats or stats[0] is None:
        total_plays, avg_time, personal_best, avg_hints, avg_score = 0, 0.0, None, 0.0, 0.0
        cursor.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (str(user_id),))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (str(user_id), display_name))
    else:
        total_plays, avg_time, personal_best, avg_hints, avg_score = stats

    total_plays = total_plays or 0
    avg_time = avg_time or 0.0
    avg_hints = avg_hints or 0.0
    avg_score = avg_score or 0.0

    new_total_plays = total_plays + 1

    time_seconds = game_info.get("completion_time_seconds", 0)
    new_avg_time = ((avg_time * total_plays) + time_seconds) / new_total_plays if new_total_plays > 0 else float(time_seconds)

    is_new_pb = False
    if personal_best is None or time_seconds < personal_best:
        personal_best = time_seconds
        is_new_pb = True

    hints = game_info.get("hints_used", 0)
    new_avg_hints = ((avg_hints * total_plays) + hints) / new_total_plays if new_total_plays > 0 else float(hints)

    score = game_info.get("score", 0)
    new_avg_score = ((avg_score * total_plays) + score) / new_total_plays if new_total_plays > 0 else float(score)

    cursor.execute("""
        UPDATE player_stats
        SET display_name = ?, word_salad_total_plays = ?, word_salad_avg_time = ?, word_salad_personal_best_time = ?, word_salad_avg_hints = ?, word_salad_avg_score = ?
        WHERE user_id = ?
    """, (display_name, new_total_plays, new_avg_time, personal_best, new_avg_hints, new_avg_score, str(user_id)))

    conn.commit()
    conn.close()

    return {
        "total_plays": new_total_plays,
        "avg_time": new_avg_time,
        "is_new_pb": is_new_pb,
        "personal_best": personal_best,
        "avg_hints": new_avg_hints,
        "avg_score": new_avg_score
    }

def update_minute_cryptic_player_stats(user_id, display_name, game_info):
    """Update player stats for Minute Cryptic after a new score is submitted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT minute_cryptic_total_plays, minute_cryptic_solved, minute_cryptic_avg_score FROM player_stats WHERE user_id = ?", (str(user_id),))
    stats = cursor.fetchone()

    if not stats or stats[0] is None:
        total_plays, solved_count, avg_score = 0, 0, 0.0
        cursor.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (str(user_id),))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (str(user_id), display_name))
    else:
        total_plays, solved_count, avg_score = stats

    total_plays = total_plays or 0
    solved_count = solved_count or 0
    avg_score = avg_score or 0.0

    new_total_plays = total_plays + 1

    was_solved = game_info.get("solved", False)
    new_solved_count = solved_count + (1 if was_solved else 0)

    score = game_info.get("score_value", 0)
    new_avg_score = ((avg_score * total_plays) + score) / new_total_plays if new_total_plays > 0 else float(score)

    cursor.execute("""
        UPDATE player_stats
        SET display_name = ?, minute_cryptic_total_plays = ?, minute_cryptic_solved = ?, minute_cryptic_avg_score = ?
        WHERE user_id = ?
    """, (display_name, new_total_plays, new_solved_count, new_avg_score, str(user_id)))

    conn.commit()
    conn.close()

    return {
        "total_plays": new_total_plays,
        "solved_count": new_solved_count,
        "avg_score": new_avg_score
    }

def update_pips_player_stats(user_id, display_name, game_info):
    """Update player stats for Pips after a new score is submitted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT pips_total_score, pips_total_cookies FROM player_stats WHERE user_id = ?", (str(user_id),))
    stats = cursor.fetchone()

    if not stats or stats[0] is None:
        total_score, total_cookies = 0, 0
        cursor.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (str(user_id),))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO player_stats (user_id, display_name) VALUES (?, ?)", (str(user_id), display_name))
    else:
        total_score, total_cookies = stats

    total_score = total_score or 0
    total_cookies = total_cookies or 0

    new_total_score = total_score + game_info.get("score", 0)
    new_total_cookies = total_cookies + (1 if game_info.get("cookie", False) else 0)

    cursor.execute("""
        UPDATE player_stats
        SET display_name = ?, pips_total_score = ?, pips_total_cookies = ?
        WHERE user_id = ?
    """, (display_name, new_total_score, new_total_cookies, str(user_id)))

    conn.commit()

    # For pips, we also need to fetch all scores for the current game to generate the post.
    game_number = game_info.get("game_number")
    scores = get_pips_scores_for_game(user_id, game_number)

    conn.close()

    return {
        "total_score": new_total_score,
        "total_cookies": new_total_cookies,
        "scores": [dict(row) for row in scores]
    }
    
def save_minute_cryptic_score(user_id: int, display_name: str, game_date: str, clue: str, word_length: int, score_description: str):
    """Saves a Minute Cryptic score to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    try:
        cursor.execute("""
            INSERT INTO minute_cryptic_scores (
                user_id, display_name, game_date, clue, word_length,
                score_description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            display_name,
            game_date,
            clue,
            word_length,
            score_description,
            created_at
        ))
        conn.commit()
        print(f"DB: Saved Minute Cryptic score for {display_name} on {game_date}")
    except sqlite3.Error as e:
        print(f"Database error in save_minute_cryptic_score: {e}")
    finally:
        conn.close()

def save_word_salad_score(user_id: int, display_name: str, game_number: int,
                         completion_time_seconds: int, hints_used: int, score: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    # Check if a score for this user and puzzle already exists
    cursor.execute("""
        SELECT 1 FROM word_salad_scores
        WHERE user_id = ? AND game_number = ?
    """, (user_id, game_number))
    existing_score = cursor.fetchone()

    if existing_score:
        # Update all fields, including the new 'score'
        cursor.execute("""
            UPDATE word_salad_scores
            SET display_name = ?, completion_time_seconds = ?, hints_used = ?, score = ?, created_at = ?
            WHERE user_id = ? AND game_number = ?
        """, (display_name, completion_time_seconds, hints_used, score, created_at,
              user_id, game_number))
        print(f"Updated Word Salad score for {display_name} (Game #{game_number}).")
    else:
        cursor.execute("""
            INSERT INTO word_salad_scores
            (user_id, display_name, game_number, completion_time_seconds, hints_used, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, display_name, game_number, completion_time_seconds, hints_used, score, created_at))
        print(f"Added Word Salad score for {display_name} (Game #{game_number}).")

    conn.commit()
    conn.close()

def get_scores_by_period(period: str, column_name: str = 'created_at') -> tuple[str, ...]:
    """Helper function to get the WHERE clause and parameters for a given period."""
    # Use DATE() with localtime to correctly handle timezones for weekly/monthly cutoffs
    today = datetime.date.today()
    if period == 'weekly':
        # Go back to the most recent Monday (weekday 0)
        start_of_week = today - timedelta(days=today.weekday())
        start_date = start_of_week.isoformat()
        return f"WHERE DATE({column_name}, 'localtime') >= DATE(?)", (start_date,)
    elif period == 'monthly':
        # First day of the current month
        start_of_month = today.replace(day=1)
        start_date = start_of_month.isoformat()
        return f"WHERE DATE({column_name}, 'localtime') >= DATE(?)", (start_date,)
    else:  # overall
        return "", ()

def get_wordle_leaderboard(period: str = 'weekly'):
    """Fetch enhanced Wordle leaderboard data with superlatives."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period(period, 'created_at')

    # 1. Get top 3 players by SUM(total_score)
    cursor.execute(f"""
        SELECT display_name, SUM(total_score) as total_score
        FROM wordle_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY total_score DESC
        LIMIT 3
    """, params)
    top_players = cursor.fetchall()

    # 2. Get superlatives
    # Highest AVG(skill)
    cursor.execute(f"""
        SELECT display_name, AVG(skill) as avg_skill
        FROM wordle_scores
        {where_clause}
        GROUP BY user_id, display_name
        HAVING COUNT(user_id) > 3
        ORDER BY avg_skill DESC
        LIMIT 1
    """, params)
    einstein = cursor.fetchone()

    # Highest AVG(luck)
    cursor.execute(f"""
        SELECT display_name, AVG(luck) as avg_luck
        FROM wordle_scores
        {where_clause}
        GROUP BY user_id, display_name
        HAVING COUNT(user_id) > 3
        ORDER BY avg_luck DESC
        LIMIT 1
    """, params)
    lucky_charm = cursor.fetchone()

    # Highest current_streak from player_stats
    cursor.execute("""
        SELECT display_name, current_streak
        FROM player_stats
        ORDER BY current_streak DESC
        LIMIT 1
    """)
    ironman = cursor.fetchone()

    conn.close()

    return {
        "top_players": top_players,
        "einstein": einstein,
        "lucky_charm": lucky_charm,
        "ironman": ironman
    }

def _parse_uniqueness_to_int(uniqueness_text: str) -> int:
    if not uniqueness_text:
        return 0
    uniqueness_text = uniqueness_text.lower().replace(",", "")
    if "million" in uniqueness_text:
        return 1000000
    if "in" in uniqueness_text:
        parts = uniqueness_text.split(" in ")
        if len(parts) == 2:
            try:
                return int(parts[1])
            except (ValueError, IndexError):
                return 0
    return 0

def get_connections_leaderboard(period: str = 'weekly'):
    """Fetch enhanced Connections leaderboard data with superlatives."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    where_clause, params = get_scores_by_period(period, "created_at")

    # 1. Get top 3 players by SUM(total_score)
    cursor.execute(f"""
        SELECT display_name, SUM(total_score) as total_score
        FROM connections_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY total_score DESC
        LIMIT 3
    """, params)
    top_players = cursor.fetchall()

    # 2. Get superlatives
    # The Perfector
    cursor.execute(f"""
        SELECT display_name, SUM(perfect_game) as perfect_games
        FROM connections_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY perfect_games DESC
        LIMIT 1
    """, params)
    perfector = cursor.fetchone()

    # The Grandmaster
    cursor.execute(f"""
        SELECT display_name, SUM(solved_purple_first) as purple_firsts
        FROM connections_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY purple_firsts DESC
        LIMIT 1
    """, params)
    grandmaster = cursor.fetchone()

    # The Pathfinder
    # Build uniqueness filter correctly
    if where_clause:
        uniqueness_where = f"{where_clause} AND uniqueness_text IS NOT NULL"
    else:
        uniqueness_where = "WHERE uniqueness_text IS NOT NULL"

    cursor.execute(f"""
        SELECT display_name, uniqueness_text
        FROM connections_scores
        {uniqueness_where}
    """, params)
    uniqueness_scores = cursor.fetchall()

    pathfinder = None
    if uniqueness_scores:
        max_rarity = -1
        best_score = None
        for display_name, uniqueness_text in uniqueness_scores:
            rarity = _parse_uniqueness_to_int(uniqueness_text)
            if rarity > max_rarity:
                max_rarity = rarity
                best_score = (display_name, uniqueness_text)
        pathfinder = best_score

    conn.close()

    return {
        "top_players": top_players,
        "perfector": perfector,
        "grandmaster": grandmaster,
        "pathfinder": pathfinder
    }

def get_framed_leaderboard(period: str = 'overall'):
    """Fetch Framed leaderboard data, supporting different periods and stats."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period(period, 'created_at')

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

def get_gisnep_leaderboard(period: str = 'weekly'):
    """Fetch enhanced Gisnep leaderboard data with superlatives."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Get top 10 players by average solve time for the specified period
    where_clause, params = get_scores_by_period(period, "created_at")

    cursor.execute(f"""
        SELECT
            ps.display_name,
            ps.gisnep_avg_seconds
        FROM player_stats ps
        JOIN (SELECT DISTINCT user_id FROM gisnep_scores {where_clause}) as period_players
        ON ps.user_id = period_players.user_id
        WHERE ps.gisnep_total_plays > 0
        ORDER BY ps.gisnep_avg_seconds ASC
        LIMIT 10
    """, params)
    top_players = cursor.fetchall()

    # 2. Get superlatives for the week
    mercury_award = None
    scholar_award = None
    if period == 'weekly':
        weekly_where_clause, weekly_params = get_scores_by_period('weekly', column_name='created_at')

        # The Mercury Award: Fastest single solve of the week
        cursor.execute(f"""
            SELECT display_name, MIN(completion_time) as fastest_time
            FROM gisnep_scores
            {weekly_where_clause}
            GROUP BY user_id, display_name
            ORDER BY fastest_time ASC
            LIMIT 1
        """, weekly_params)
        mercury_award = cursor.fetchone()

        # The Scholar Award: Completed all 7 puzzles this week
        cursor.execute(f"""
            SELECT display_name, COUNT(DISTINCT game_number) as puzzles_solved
            FROM gisnep_scores
            {weekly_where_clause}
            GROUP BY user_id, display_name
            HAVING puzzles_solved >= 7
            ORDER BY puzzles_solved DESC
            LIMIT 1
        """, weekly_params)
        scholar_award = cursor.fetchone()

    conn.close()

    return {
        "top_players": top_players,
        "mercury_award": mercury_award,
        "scholar_award": scholar_award
    }

def get_bandle_leaderboard(period: str = 'weekly'):
    """Fetch enhanced Bandle leaderboard data with superlatives."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    where_clause, params = get_scores_by_period(period, "created_at")

    # 1. Get top 3 players by average attempts
    cursor.execute(f"""
        SELECT
            p.display_name,
            p.bandle_avg_attempts,
            p.bandle_avg_bonus_rounds
        FROM player_stats p
        JOIN (SELECT DISTINCT user_id FROM bandle_scores {where_clause}) as period_players
        ON p.user_id = period_players.user_id
        WHERE p.bandle_total_plays > 0
        ORDER BY p.bandle_avg_attempts ASC
        LIMIT 3
    """, params)
    top_players = cursor.fetchall()

    # 2. Get all scores for the period to calculate superlatives
    cursor.execute(f"SELECT user_id, display_name, bonus_emojis FROM bandle_scores {where_clause}", params)
    scores = cursor.fetchall()

    # 3. Calculate superlatives
    player_emoji_counts = {}
    for user_id, display_name, emojis in scores:
        if user_id not in player_emoji_counts:
            player_emoji_counts[user_id] = {"display_name": display_name, "counts": {}}

        for emoji in emojis.split():
            player_emoji_counts[user_id]["counts"][emoji] = player_emoji_counts[user_id]["counts"].get(emoji, 0) + 1

    # Superlative logic
    music_historian = None
    ar_scout = None
    producers_ear = None
    superfan = None

    max_hist_score = 0
    max_ar_score = 0
    max_prod_score = 0
    max_fan_score = 0

    for user_id, data in player_emoji_counts.items():
        counts = data["counts"]
        display_name = data["display_name"]

        hist_score = counts.get("🧩", 0) + counts.get("📅", 0)
        if hist_score > max_hist_score:
            max_hist_score = hist_score
            music_historian = (display_name, hist_score)

        ar_score = counts.get("🧑", 0) + counts.get("🖼️", 0)
        if ar_score > max_ar_score:
            max_ar_score = ar_score
            ar_scout = (display_name, ar_score)

        prod_score = counts.get("🎸", 0) + counts.get("⏱️", 0)
        if prod_score > max_prod_score:
            max_prod_score = prod_score
            producers_ear = (display_name, prod_score)

        fan_score = counts.get("🎤", 0) + counts.get("💿", 0)
        if fan_score > max_fan_score:
            max_fan_score = fan_score
            superfan = (display_name, fan_score)

    # Get Rock God (highest max_streak)
    cursor.execute("SELECT display_name, max_streak FROM player_stats ORDER BY max_streak DESC LIMIT 1")
    rock_god = cursor.fetchone()

    conn.close()

    return {
        "top_players": top_players,
        "music_historian": music_historian,
        "ar_scout": ar_scout,
        "producers_ear": producers_ear,
        "superfan": superfan,
        "rock_god": rock_god
    }

def get_minute_cryptic_leaderboard(period: str = 'weekly') -> list[tuple[str, int]]:
    """
    Fetches the Minute Cryptic leaderboard data, supporting different periods and stats.
    Currently counts number of puzzles solved (score_value = 0) in the given period.
    Also fetches average score.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period(period, 'created_at')

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
    where_clause, params = get_scores_by_period(period, 'created_at')

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
        ORDER BY avg_score DESC, total_score DESC, games_played DESC
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def get_sexaginta_leaderboard(period="weekly"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period(period, "created_at")

    # Top players
    cursor.execute(f"""
        SELECT display_name, AVG(percent_solved) as avg_pct, AVG(game_score) as avg_score, COUNT(*) as plays
        FROM sexaginta_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY avg_pct DESC, avg_score DESC
        LIMIT 10
    """, params)
    top_players = cursor.fetchall()

    # Superlatives
    # The Strategist: Player with the highest average game score.
    cursor.execute(f"""
        SELECT display_name, AVG(game_score) as avg_score
        FROM sexaginta_scores
        {where_clause}
        GROUP BY user_id, display_name
        HAVING COUNT(*) > 3
        ORDER BY avg_score DESC
        LIMIT 1
    """, params)
    strategist = cursor.fetchone()

    # The Finisher: Player with the highest average percent solved.
    cursor.execute(f"""
        SELECT display_name, AVG(percent_solved) as avg_pct
        FROM sexaginta_scores
        {where_clause}
        GROUP BY user_id, display_name
        HAVING COUNT(*) > 3
        ORDER BY avg_pct DESC
        LIMIT 1
    """, params)
    finisher = cursor.fetchone()

    # The Veteran: Player with the most plays.
    cursor.execute(f"""
        SELECT display_name, COUNT(*) as plays
        FROM sexaginta_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY plays DESC
        LIMIT 1
    """, params)
    veteran = cursor.fetchone()

    conn.close()
    return {
        "top_players": top_players,
        "strategist": strategist,
        "finisher": finisher,
        "veteran": veteran
    }

def get_pips_leaderboard(period: str = 'overall'):
    """Fetch Pips leaderboard data, supporting different periods and stats."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    where_clause, params = get_scores_by_period(period, 'created_at')

    # Fetch relevant stats for Pips
    cursor.execute(f"""
        SELECT display_name,
               SUM(score) AS total_score,
               COUNT(*) AS games_played,
               SUM(cookie) AS cookie_count
        FROM pips_scores
        {where_clause}
        GROUP BY user_id, display_name
        ORDER BY cookie_count DESC, total_score DESC
        LIMIT 10
    """, params)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def get_pips_completed_difficulties(user_id: int, game_number: int) -> list[str]:
    """
    Retrieves the list of difficulties a user has completed for a specific Pips game.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT difficulty FROM pips_scores
        WHERE user_id = ? AND game_number = ?
    """, (user_id, game_number))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_pips_scores_for_game(user_id: int, game_number: int) -> list:
    """
    Retrieves all scores for a user for a specific Pips game number.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT difficulty, completion_time, score, cookie FROM pips_scores
        WHERE user_id = ? AND game_number = ?
        ORDER BY CASE difficulty WHEN 'easy' THEN 1 WHEN 'medium' THEN 2 WHEN 'hard' THEN 3 END
    """, (user_id, game_number))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_wordle_stats(user_id: int) -> dict:
    """Fetches Wordle statistics for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), AVG(attempts), AVG(total_score)
        FROM wordle_scores
        WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return {
        "games_played": stats[0] or 0,
        "avg_attempts": stats[1] or 0,
        "avg_score": stats[2] or 0
    }

def get_connections_stats(user_id: int) -> dict:
    """Fetches Connections statistics for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), AVG(total_score)
        FROM connections_scores
        WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return {
        "games_played": stats[0] or 0,
        "avg_score": stats[1] or 0
    }

def get_framed_stats(user_id: int) -> dict:
    """Fetches Framed statistics for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), AVG(attempts), AVG(total_score)
        FROM framed_scores
        WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return {
        "games_played": stats[0] or 0,
        "avg_attempts": stats[1] or 0,
        "avg_score": stats[2] or 0
    }

def get_gisnep_stats(user_id: int) -> dict:
    """Fetches Gisnep statistics for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), AVG(completion_time)
        FROM gisnep_scores
        WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return {
        "games_played": stats[0] or 0,
        "avg_time": stats[1] or 0
    }

def get_player_sexaginta_stats(user_id: int) -> dict:
    """
    Fetches basic Sexaginta-Quattuordle stats for a single player.
    Returns a dictionary with total plays, and average percent solved.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Query aggregate stats for this player
    cursor.execute("""
        SELECT COUNT(*), AVG(percent_solved)
        FROM sexaginta_scores
        WHERE user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return {"total_plays": 0, "avg_pct": 0.0}

    total_plays, avg_pct = result

    return {
        "total_plays": total_plays or 0,
        "avg_pct": avg_pct or 0.0
    }

def get_gisnep_puzzle_stats(game_number: int) -> dict:
    """Fetches the stats for a specific Gisnep puzzle."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT total_solves, avg_seconds
        FROM gisnep_puzzle_stats
        WHERE game_number = ?
    """, (game_number,))
    stats = cursor.fetchone()
    conn.close()
    if stats:
        return {
            "total_solves": stats[0],
            "avg_seconds": stats[1]
        }
    return {
        "total_solves": 0,
        "avg_seconds": 0.0
    }

def get_player_gisnep_stats(user_id: str) -> dict:
    """Fetches Gisnep-specific stats for a given user from the player_stats table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT gisnep_total_plays, gisnep_avg_seconds, gisnep_personal_best_seconds
        FROM player_stats
        WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    conn.close()
    if stats:
        return {
            "total_plays": stats[0] or 0,
            "avg_seconds": stats[1] or 0.0,
            "personal_best": stats[2]
        }
    return {
        "total_plays": 0,
        "avg_seconds": 0.0,
        "personal_best": None
    }

def get_bandle_stats(user_id: int) -> dict:
    """Fetches Bandle statistics for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), AVG(attempts), SUM(bonus_rounds_completed)
        FROM bandle_scores
        WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return {
        "games_played": stats[0] or 0,
        "avg_attempts": stats[1] or 0,
        "total_bonus": stats[2] or 0
    }

def get_minute_cryptic_stats(user_id: int) -> dict:
    """Fetches Minute Cryptic statistics for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), AVG(score_value)
        FROM minute_cryptic_scores
        WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return {
        "games_played": stats[0] or 0,
        "avg_score": stats[1] or 0
    }

def get_word_salad_stats(user_id: int) -> dict:
    """Fetches Word Salad statistics for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), AVG(completion_time_seconds), AVG(score)
        FROM word_salad_scores
        WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return {
        "games_played": stats[0] or 0,
        "avg_time": stats[1] or 0,
        "avg_score": stats[2] or 0
    }

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
    now = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") # Changed to now(timezone.utc)
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
    now = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") # Changed to now(timezone.utc)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM user_roles WHERE expires_at < ?
    ''', (now,))
    conn.commit()
    conn.close()

def get_overall_recent_wordle_scores(limit=5):
    """
    Fetches the most recent Wordle scores from all users, ordered by created_at descending,
    limited to the specified number.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT game_number, attempts, skill, luck, created_at
            FROM wordle_scores
            ORDER BY created_at DESC
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
    ordered by created_at descending, limited to the specified number.
    Returns a list of tuples, each containing (puzzle_number, created_at).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT game_number, created_at
            FROM connections_scores
            ORDER BY created_at DESC
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
