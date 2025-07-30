import json
import os
import praw
import time

POST_LIMIT = 15
SUBREDDITS = [
    "aviation",
]

with open("airports.json") as f:
    airports = json.load(f)

with open("logs.json") as f:
    logs = json.load(f)


def find_mentioned_airports(text: str) -> list[dict]:
    mentioned = []

    for airport in airports.values():
        identifiers = [
            airport["name"],
            airport["icao"],
            airport["iata"],
        ]
        if any(identifier in text for identifier in identifiers if identifier):
            mentioned.append(airport)

    return mentioned


def make_comment_body(airports: list[dict]) -> str:
    table = "|IATA|ICAO|Name|Location|\n|:-|:-|:-|:-|"

    for airport in airports:
        name = airport["name"]
        icao = airport["icao"]
        iata = airport["iata"]

        flightradar = f"https://www.flightradar24.com/airport/{icao.lower()}"
        name_col = f"[{name}]({flightradar})"

        city = airport["city"]
        state = airport["state"]
        country = airport["country"]

        location = ",".join(x for x in [city, state, country] if x)

        table += f"\n|{iata}|{icao}|{name_col}|{location}|"

    table += "\n\n*I am a bot.*"

    return table


def run() -> None:
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_BOT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_BOT_CLIENT_SECRET"],
        username=os.environ["REDDIT_BOT_USERNAME"],
        password=os.environ["REDDIT_BOT_PASSWORD"],
    )

    try:
        for subreddit_name in SUBREDDITS:
            subreddit = reddit.subreddit(subreddit_name)

            for submission in subreddit.new(limit=POST_LIMIT):
                if submission.id in logs:
                    continue

                print("ID", submission.id)
                print("Title", submission.title)
                print("Created", submission.created_utc)

                mentioned_airports = find_mentioned_airports(submission.title + submission.selftext)

                if not mentioned_airports:
                    print("No airports mentioned in submission")
                    continue

                comment_body = make_comment_body(mentioned_airports)
                print("COMMENT BODY:")
                print(comment_body)
                print()
                # submission.reply(comment_body)

                logs[submission.id] = {
                    "subreddit": subreddit_name,
                    "title": submission.title,
                    "created_at": submission.created_utc,
                    "mentioned_icao_codes": [a["icao"] for a in mentioned_airports],
                }

                time.sleep(2)
    finally:
        with open("logs.json", "w") as f:
            json.dump(logs, f, indent=4)
