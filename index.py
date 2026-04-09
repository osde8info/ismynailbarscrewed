import os
import pandas as pd
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "nailbars.csv")


def load_data():
    df = pd.read_csv(DATA_PATH)
    return df


def screwed_label(score):
    if score >= 125:
        return "royally screwed", "danger"
    if score >= 110:
        return "pretty screwed", "warning"
    if score >= 95:
        return "a bit screwed", "info"
    return "doing alright", "success"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    query = request.args.get("q", "").strip().upper()
    if not query:
        return render_template("index.html", error="Please enter a postcode or town.")

    df = load_data()
    # Match on postcode prefix or full postcode or town (case-insensitive)
    mask = (
        df["postcode"].str.upper().str.startswith(query)
        | df["postcode"].str.upper().str.replace(" ", "").str.startswith(query.replace(" ", ""))
        | df["town"].str.upper().str.contains(query, na=False)
        | df["region"].str.upper().str.contains(query, na=False)
    )
    results = df[mask].copy()

    if results.empty:
        return render_template(
            "results.html",
            query=query,
            results=[],
            count=0,
        )

    results = results.sort_values("screwed_score", ascending=False)
    rows = []
    for _, row in results.iterrows():
        label, badge = screwed_label(row["screwed_score"])
        rows.append(
            {
                "name": row["name"],
                "address": row["address"],
                "postcode": row["postcode"],
                "town": row["town"],
                "rateable_value": row["rateable_value"],
                "screwed_score": row["screwed_score"],
                "label": label,
                "badge": badge,
            }
        )

    return render_template(
        "results.html",
        query=query,
        results=rows,
        count=len(rows),
    )


@app.route("/leaderboard")
def leaderboard():
    df = load_data()
    top = df.sort_values("screwed_score", ascending=False).head(100).copy()
    rows = []
    for rank, (_, row) in enumerate(top.iterrows(), start=1):
        label, badge = screwed_label(row["screwed_score"])
        rows.append(
            {
                "rank": rank,
                "name": row["name"],
                "address": row["address"],
                "postcode": row["postcode"],
                "town": row["town"],
                "region": row["region"],
                "rateable_value": row["rateable_value"],
                "screwed_score": row["screwed_score"],
                "label": label,
                "badge": badge,
            }
        )
    return render_template("leaderboard.html", rows=rows)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, "robots.txt")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
