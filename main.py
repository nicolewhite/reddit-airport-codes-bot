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


def find_mentioned_icao_codes(text: str) -> set[str]:
    mentioned = set()

    for key, airport in airports.items():
        if airport["name"] in text:
            mentioned.add(key)
            continue

        for code in (airport["icao"], airport["iata"]):
            if text.startswith(f"{code} ") or text.endswith(f" {code}") or f" {code} " in text:
                mentioned.add(key)
                break

    return mentioned


def make_comment_body(icao_codes: set[str]) -> str:
    table = "|IATA|ICAO|Name|Location|\n|:-|:-|:-|:-|"

    for code in sorted(icao_codes):
        airport = airports[code]

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
        user_agent=f"{os.environ["REDDIT_BOT_USERNAME"]}/1.0",
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

                mentioned_icao_codes = set().union(*[
                    find_mentioned_icao_codes(submission.title),
                    find_mentioned_icao_codes(submission.selftext),
                ])

                if not mentioned_icao_codes:
                    print("No airports mentioned in submission")
                    continue

                comment_body = make_comment_body(mentioned_icao_codes)
                print("COMMENT BODY:")
                print(comment_body)
                print()
                # submission.reply(comment_body)

                logs[submission.id] = {
                    "subreddit": subreddit_name,
                    "title": submission.title,
                    "created_at": submission.created_utc,
                    "mentioned_icao_codes": mentioned_icao_codes,
                }

                time.sleep(2)
    finally:
        with open("logs.json", "w") as f:
            json.dump(logs, f, indent=4)


if __name__ == "__main__":
    run()
