import praw
import json
import os
import sys
import dateparser
import logging
import datetime
import re
import enum

import praw.exceptions

from discord_webhook import DiscordWebhook, DiscordEmbed

import helpers

from config import *

db = {}

def load_json(filename: str):
    try:
        with open(filename, "r") as file:
            if file.readable(): # Check for corruption
                try:
                    return json.load(file)
                except:
                    raise FileNotFoundError
            else:
                logging.warning("Broken file detected!")
                return {}
    except FileNotFoundError as e:
        logging.warning(f"Error opening db: {e} - Returning no DB")
        return {}

def save_json(db: dict, filename: str):
    with open(filename, "w") as file:
        json.dump(db, file)

class Reddit_Handler:
    def __init__(self):
        global db

        db = load_json("db.json")
        self.reddit = None

        self.login()

        self.tsrotd = TSROTD(self.reddit)

    def login(self):
        """
        Logs into reddit, sys.exists on error.
        """
        try:
            self.reddit = praw.Reddit(
                client_id = id,
                client_secret = secret,
                user_agent = "linux:srotd:v0.1-dev (By /u/_tomGER)",
                username = "r_tomBOT",
                password = password)
        except praw.exceptions.RedditAPIException as e:
            logging.critical(f"Error in login: {e}")
            sys.exit()

        logging.info(f"Login as: {self.reddit.user.me()}")

    def exit(self):
        save_json(db, "db.json")
        logging.info("Saved DB")

class TSROTD:
    """
    TinySubredditOfTheDay Subclass
    
    Requires RedditHandler!
    """
    def __init__(self, reddit):
        self.reddit = reddit
        self.sub = reddit.subreddit("tsrotd_dev")

    def search_for_dates(self, submission: praw.Reddit.submission):
        global db
        
        if (date := helpers.parse_date_from_string(submission.title)) != None \
        and helpers.check_if_date_valid(date):
            logging.info(f"Found valid submission date in title of: {submission.id}")
            db[submission.id]["date"] = {}
            db[submission.id]["date"] = helpers.parse_date(date)
            
        if submission.num_comments > 0:
            for comment in submission.comments:
                if "[date]" in comment.body.lower() \
                and (date := helpers.parse_date_from_string(comment.body)) != None \
                and helpers.check_if_date_valid(date):
                    logging.info(f"Found date comment for {submission.id}: {comment.id}")    
                    
                    db[submission.id]["date"] = {}
                    db[submission.id]["date"] = helpers.parse_date(date)
    
    def check_for_title(self, submission: praw.Reddit.submission):
        global db
        
        for comment in submission.comments:
            if not "[title]" in comment.body.lower():
                continue
    
            logging.info(f"Found title comment for {submission.id}: {comment.id}")
            title = comment.body.replace("[title]", "", 1).strip()
            
            db[submission.id]["title"] = title

    def check_for_sub(self, submission: praw.Reddit.submission):
        for x in submission.title.split():          
            if (match := re.match(r"^[r]\/|^\/[r]\/", x)):
                title = x.replace(match.group(0), "").strip()
                logging.info(f"Found subreddit name of: {title}")
                
                return title

    def check_for_new_posts(self):
        global db

        for submission in self.sub.new(limit=15):
            logging.debug(f"Going through submission: {submission.title}")
            
            if submission.link_flair_text != "BOT READY":
                continue
            
            logging.info("Found BOT READY submission!")
            
            if not submission.id in db.keys():
                db[submission.id] = {}
            
            self.search_for_dates(submission)
            self.check_for_title(submission)
            if (sub := self.check_for_sub(submission)) != "":
                db[submission.id]["sub"] = sub

class DiscordHelper:
    def __init__(self, webhook_url: str):
        # Extract from config.py
        self.webhook = DiscordWebhook(url = webhook_url, username = discord_username)
        self.embed = DiscordEmbed()
            
    def basic_message(self, title: str, message: str, color):
        if isinstance(color, Color):
            color = color.value
        
        logging.info(color)
        self.embed = DiscordEmbed(
            title = title,
            description = message,
            color = color
        )
    
    def send_message(self):
        self.webhook.add_embed(self.embed)
        self.webhook.execute(True, True)
        self.embed = DiscordEmbed()

class Color(enum.Enum):
    red = "ff0000"
    green = "00dd1f"
    gray = "a0a0a0"   

def main():
    logging.root.handlers = []
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )
    
    reddit = Reddit_Handler()
    reddit.tsrotd.check_for_new_posts()
    
    discord = DiscordHelper(discord_webhook)
    discord.basic_message("Bot has started.", "Pog", Color.gray)
    discord.send_message()
    
    reddit.exit()

if __name__ == "__main__":
    main()