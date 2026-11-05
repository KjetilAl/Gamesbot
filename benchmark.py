import timeit

def original(display_name, game_info, player_stats):
    game_number = game_info.get("game_number", "?")
    scores = player_stats.get("scores")

    if not scores:
        return f"🏆 **{display_name}** is making progress on Pips #{game_number}!"

    total_score = sum(s['score'] for s in scores)
    cookie_count = sum(s['cookie'] for s in scores)

    message = f"🏆 **{display_name}** has completed all Pips difficulties for game #{game_number} with a total score of **{total_score}**!\n\n"

    for score in scores:
        time_min = score['completion_time'] // 60
        time_sec = score['completion_time'] % 60
        time_str = f"{time_min}:{time_sec:02d}"
        message += f"**{score['difficulty'].capitalize()}**: {time_str} ({score['score']} pts)"
        if score.get('cookie'):
            message += " 🍪"
        message += "\n"

    if cookie_count > 0:
        message += f"\nWow, {cookie_count} cookie{'s' if cookie_count > 1 else ''}! You're a top performer! 🍪"

    return message


def optimized(display_name, game_info, player_stats):
    game_number = game_info.get("game_number", "?")
    scores = player_stats.get("scores")

    if not scores:
        return f"🏆 **{display_name}** is making progress on Pips #{game_number}!"

    total_score = 0
    cookie_count = 0
    details = []

    for score in scores:
        total_score += score['score']
        cookie_count += score['cookie']

        time_min = score['completion_time'] // 60
        time_sec = score['completion_time'] % 60
        time_str = f"{time_min}:{time_sec:02d}"

        line = f"**{score['difficulty'].capitalize()}**: {time_str} ({score['score']} pts)"
        if score.get('cookie'):
            line += " 🍪"
        details.append(line)

    message = f"🏆 **{display_name}** has completed all Pips difficulties for game #{game_number} with a total score of **{total_score}**!\n\n"
    message += "\n".join(details) + "\n"

    if cookie_count > 0:
        message += f"\nWow, {cookie_count} cookie{'s' if cookie_count > 1 else ''}! You're a top performer! 🍪"

    return message

display_name = "PlayerOne"
game_info = {"game_number": "42"}
player_stats = {
    "scores": [
        {"difficulty": "easy", "score": 100, "cookie": 1, "completion_time": 125},
        {"difficulty": "medium", "score": 250, "cookie": 0, "completion_time": 340},
        {"difficulty": "hard", "score": 500, "cookie": 1, "completion_time": 612},
        {"difficulty": "expert", "score": 1000, "cookie": 1, "completion_time": 950},
    ]
}

if original(display_name, game_info, player_stats) != optimized(display_name, game_info, player_stats):
    print("Mismatch!")
    print(original(display_name, game_info, player_stats))
    print(optimized(display_name, game_info, player_stats))

import time
start = time.perf_counter()
for _ in range(100000):
    original(display_name, game_info, player_stats)
orig_time = time.perf_counter() - start

start = time.perf_counter()
for _ in range(100000):
    optimized(display_name, game_info, player_stats)
opt_time = time.perf_counter() - start

print(f"Original:  {orig_time:.4f}s")
print(f"Optimized: {opt_time:.4f}s")
print(f"Improvement: {(orig_time - opt_time) / orig_time * 100:.2f}%")
