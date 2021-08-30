import praw
import json
import os
import sys

import praw.exceptions

from config import id, secret, password

def load_json(filename: str):
    try:
        with open(filename, "r") as file:
            if file.readable(): # Check for corruption
                try:
                    return json.load(file)
                except:
                    raise FileNotFoundError
            else:
                print("Broken file detected!")
                return {}
    except FileNotFoundError as e:
        print(f"Error opening db: {e} - Returning no DB")
        return {}

def save_json(db: dict, filename: str):
    with open(filename, "w") as file:
        json.dump(db, file)

class Reddit_Handler:
    def __init__(self):
        self.db = load_json("db.json")
        self.reddit = None

        self.login()

    def login(self):
        try:
            self.reddit = praw.Reddit(
                client_id = id,
                client_secret = secret,
                user_agent = "linux:srotd:v0.1-dev (By /u/_tomGER)",
                username = "r_tomBOT",
                password = password)
        except praw.exceptions.RedditAPIException as e:
            print(f"Error in login: {e}")
            sys.exit()

        print(f"Login as: {self.reddit.user.me()}")

    def check_for_new_posts(self):
        for submission in self.reddit.subreddit("tsrotd_dev").new(limit=15):
            if submission.id in self.db.keys():
                continue

            self.db[submission.id] = True

    def exit(self):
        save_json(self.db, "db.json")
        print("Saved DB")

def main():
    reddit = Reddit_Handler()
    reddit.check_for_new_posts()

    reddit.exit()

if __name__ == "__main__":
    main()