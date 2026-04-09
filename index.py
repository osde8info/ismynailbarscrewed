import os
import pandas as pd
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, "data", "nailbars.csv"))

df["_postcode_norm"] = df["postcode"].str.replace(" ", "", regex=False).str.lower()
df["_town_lower"] = df["town"].str.lower()

total_bars = len(df)
closed_at_risk = len(df[df["status"].isin(["Closed", "At Risk", "Permanently Closed"])])
pct_screwed = round((closed_at_risk / total_bars) * 100) if total_bars else 0
towns_covered = df["town"].nunique()


@app.route("/")
def index():
    return render_template(
        "index.html",
        total_bars=total_bars,
        pct_screwed=pct_screwed,
        towns_covered=towns_covered,
    )


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        results = []
        count = 0
    else:
        q_norm = query.replace(" ", "").lower()
        postcode_match = df["_postcode_norm"] == q_norm
        town_match = df["_town_lower"].str.contains(query.lower(), regex=False)
        matched = df[postcode_match | town_match]
        results = matched.to_dict(orient="records")
        count = len(results)
    return render_template("results.html", query=query, results=results, count=count)


@app.route("/leaderboard")
def leaderboard():
    top20 = df.nlargest(20, "screwed_score").to_dict(orient="records")
    return render_template("leaderboard.html", leaderboard=top20)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, "robots.txt")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
