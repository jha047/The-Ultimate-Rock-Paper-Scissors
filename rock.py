import os
from flask import Flask, jsonify, render_template, request, session
import random

app = Flask(__name__)
# Render requires a static or persistent environment key for production sessions
app.secret_key = os.environ.get("SECRET_KEY", "ultimate_rps_secret_key")

# Core move lookup tables
BEATS = {"rock": "paper", "paper": "scissors", "scissors": "rock"}
LOSES_TO = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


def predict_unbeatable_move(history, rounds_data):
    """
    Super Unbeatable AI Engine combining N-gram pattern recognition,
    psychological outcome mapping, and weighted frequency analysis.
    """
    if not history:
        # Initial round choice: standard human bias heavily favors Rock (~35-40%)
        return "paper"

    predictions = {}

    # Tier 1: 3-Gram Sequence Matching (Highest Confidence)
    if len(history) >= 4:
        pattern_3 = history[-3:]
        matches_3 = []
        for i in range(len(history) - 3):
            if history[i:i + 3] == pattern_3:
                matches_3.append(history[i + 3])
        if matches_3:
            most_likely = max(set(matches_3), key=matches_3.count)
            predictions['ngram_3'] = (BEATS[most_likely], 4)

    # Tier 2: 2-Gram Sequence Matching
    if len(history) >= 3:
        pattern_2 = history[-2:]
        matches_2 = []
        for i in range(len(history) - 2):
            if history[i:i + 2] == pattern_2:
                matches_2.append(history[i + 2])
        if matches_2:
            most_likely = max(set(matches_2), key=matches_2.count)
            predictions['ngram_2'] = (BEATS[most_likely], 3)

    # Tier 3: Psychological Win-Stay / Lose-Shift Analysis
    if rounds_data:
        last_round = rounds_data[-1]
        player_last = last_round['player']
        result_last = last_round['result']

        if result_last == 'win':
            # Winner bias: Humans tend to stay with a winning move
            predictions['psychology'] = (BEATS[player_last], 3)
        elif result_last == 'loss':
            # Loser bias: Humans tend to switch to what would have beaten the opponent's move
            likely_next = BEATS[last_round['ai']]
            predictions['psychology'] = (BEATS[likely_next], 3)
        elif result_last == 'tie':
            # Tie bias: Players often switch to the move that beats their tie choice
            likely_next = BEATS[player_last]
            predictions['psychology'] = (BEATS[likely_next], 2)

    # Tier 4: Global Frequency Analysis
    most_common_player_move = max(set(history), key=history.count)
    predictions['frequency'] = (BEATS[most_common_player_move], 1)

    # Select candidate move with highest weighted score
    if predictions:
        best_candidate = max(predictions.values(), key=lambda item: item[1])[0]
        return best_candidate

    # Fallback: Weighted choice reflecting human move distributions
    return random.choices(["paper", "rock", "scissors"], weights=[0.40, 0.35, 0.25])[0]


@app.route("/", methods=["GET", "POST"])
def game():
    # Always reset to Main Menu state on initial GET request / browser refresh
    if request.method == "GET":
        session["game_started"] = False
        session["player_score"] = 0
        session["computer_score"] = 0
        session["history"] = []
        session["rounds_data"] = []

    session.setdefault("game_started", False)
    session.setdefault("player_score", 0)
    session.setdefault("computer_score", 0)
    session.setdefault("history", [])
    session.setdefault("rounds_data", [])

    player_choice = None
    computer_choice = None
    result_message = ""

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        action = data.get("action")

        if action == "start":
            session["game_started"] = True
            session["player_score"] = 0
            session["computer_score"] = 0
            session["history"] = []
            session["rounds_data"] = []

        elif action in ["rock", "paper", "scissors"]:
            player_choice = action

            # AI executes decision algorithm
            computer_choice = predict_unbeatable_move(
                session.get("history", []),
                session.get("rounds_data", [])
            )

            history = session.get("history", [])
            history.append(player_choice)
            session["history"] = history

            rounds_data = session.get("rounds_data", [])

            if player_choice == computer_choice:
                result_message = "It's a Tie! Starting new round..."
                round_res = "tie"
            elif BEATS[player_choice] == computer_choice:
                session["computer_score"] += 1
                result_message = "Computer Won this round!"
                round_res = "loss"
            else:
                session["player_score"] += 1
                result_message = "You Won this round!"
                round_res = "win"

            rounds_data.append({
                "player": player_choice,
                "ai": computer_choice,
                "result": round_res
            })
            session["rounds_data"] = rounds_data

            if request.is_json:
                return jsonify(
                    {
                        "player_choice": player_choice,
                        "computer_choice": computer_choice,
                        "player_score": session["player_score"],
                        "computer_score": session["computer_score"],
                        "result_message": result_message,
                    }
                )

        elif action == "reset":
            session["game_started"] = False
            session["player_score"] = 0
            session["computer_score"] = 0
            session["history"] = []
            session["rounds_data"] = []

    return render_template(
        "rps.html",
        game_started=session.get("game_started", False),
        player_score=session.get("player_score", 0),
        computer_score=session.get("computer_score", 0),
        player_choice=player_choice,
        computer_choice=computer_choice,
        result_message=result_message,
    )


if __name__ == "__main__":
    # Dynamically bind to the port environment variable injected by Render
    port = int(os.environ.get("PORT", 5000))
    # Binding host to '0.0.0.0' allows external production traffic to reach the app
    app.run(host="0.0.0.0", port=port)
