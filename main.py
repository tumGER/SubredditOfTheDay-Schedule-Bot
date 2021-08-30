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
                return json.load(file)
            else:
                print("Broken file detected!")
                return {}
    except FileNotFoundError as e:
        print(f"Error opening db: {e} - Returning no DB")
        return {}

def save_json(json: dict, filename: str):
    with open(filename, "w") as file:
        file = json.dump(json)

class Reddit_Handler:
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


def main():
    db = load_json("db.json")
    reddit = Reddit_Handler()
    reddit.login()

if __name__ == "__main__":
    main()