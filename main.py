###
# Copyright 2021-2024 AnnsAnn, git@annsann.eu
#
# Licensed under the EUPL, Version 1.2 or – as soon they will be approved by the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with theLicence.
#
# You may obtain a copy of the Licence at: https://joinup.ec.europa.eu/software/page/eupl
#
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and limitations under the Licence.
###

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
import prawcore.exceptions

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

        self.reddit.validate_on_submit = True

        self.tsrotd = TSROTD(self.reddit)

    def login(self):
        """
        Logs into reddit, sys.exists on error.
        """
        try:
            self.reddit = praw.Reddit(
                client_id = id,
                client_secret = secret,
                user_agent = "linux:srotd:v0.1-dev",
                username = username,
                password = password)
        except praw.exceptions.RedditAPIException as e:
            logging.critical(f"Error in login: {e}")
            sys.exit()

        logging.info(f"Login as: {self.reddit.user.me()}")

    def exit(self):
        save_json(db, "db.json")
        logging.info("Saved DB")

class ScheduleBuilder:
    def __init__(self):
        self.body = ""
        self.beginning = "=== STARTING BOT FIELD === \n\n\n Subreddit | Date | Info \n ---|---|----"
        self.ending = "\n\n Beep, boop, bap - Booing Conalfisher 24/7"
        
        self.body += self.beginning
        
    def add_field(self, key: str, value: str, details: str):
        self.body += f"\n{key} | {value} | {details}"
        
    def finish_and_return(self):
        self.body += self.ending
        return self.body
    
    def add_NEXT_POST(self, id: str):
        global db
        
        logging.info("Next post is: " + str(id))
        
        db["NEXT_POST"] = str(id)
    
    def do_the_magic(self):
        emergency_posts = []
        ready_posts = []
        
        for sub in db.keys():
            if sub in ("NEXT_POST", "LAST_POST_DAY", "HAS_POSTED_ABOUT_NO_SUB"):
                continue
            
            if not "IS_READY" in db[sub].keys():
                continue
            
            if "EMERGENCY" in db[sub].keys():
                emergency_posts.append(sub)
            else:
                ready_posts.append(sub)
        
        for i in range(0, 30):
            found_post = False
            
            if i != 0:
                date = datetime.datetime.now() + datetime.timedelta(days=i)
            else:
                date = datetime.datetime.now()
                
            day = date.day
            month = date.month
            year = date.year
            
            if db.get("LAST_POST_DAY") == None:
                db["LAST_POST_DAY"] = 0
                
            if db["LAST_POST_DAY"] == day and i == 0:
                continue
            
            for post in ready_posts:
                
                po_dt = db[post]["date"]
                
                if po_dt["day"] == day \
                and po_dt["month"] == month \
                and po_dt["year"] == year:
                    self.add_field(db[post]["sub"], f"{day}.{month}.{year}", "Scheduled")
                    logging.info(f"Found sub for {day}.{month}")
                    found_post = True
                    
                    ready_posts.remove(post)
                    
                    if i == 0:
                        self.add_NEXT_POST(post)
                    
                    break
            
            if not found_post:
                if len(emergency_posts) == 0:
                    self.add_field("No Sub Available", f"{day}.{month}.{year}", "")
                    continue
                
                if i == 0:
                    self.add_NEXT_POST(emergency_posts[0])
                
                self.add_field(db[emergency_posts[0]]["sub"], f"{day}.{month}.{year}", "Emergency")
                emergency_posts.pop(0)
                
class TSROTD:
    """
    TinySubredditOfTheDay Subclass
    
    Requires RedditHandler!
    """
    def __init__(self, reddit: praw.Reddit):
        self.reddit = reddit
        self.sub = reddit.subreddit("srotd_dev")
        self.discord = DiscordHelper(discord_webhook)
        
        self.post = PostHelper("subredditoftheday", reddit)
        
    def post_handling(self):        
        if self.post.check_time():
            self.post.send_post()

    def search_for_dates(self, submission: praw.Reddit.submission):
        global db
        
        if (date := helpers.parse_date_from_string(submission.title)) != None \
        and helpers.check_if_date_valid(date):
            logging.info(f"Found valid submission date in title of: {submission.id}")
            db[submission.id]["date"] = {}
            db[submission.id]["date"] = helpers.parse_date(date)
            
        if submission.num_comments > 0:
            for comment in submission.comments:
                comment_body = comment.body.replace("\\", "") # new.reddit.com issue
                
                if "[date]" in comment_body.lower() \
                and (date := helpers.parse_date_from_string(comment_body)) != None \
                and helpers.check_if_date_valid(date):
                    logging.info(f"Found date comment for {submission.id}: {comment.id}")    
                    
                    db[submission.id]["date"] = {}
                    db[submission.id]["date"] = helpers.parse_date(date)
    
    def check_for_title(self, submission: praw.Reddit.submission):
        global db
        
        for comment in submission.comments:
            comment_body = comment.body.replace("\\", "") # new.reddit.com issue
            
            if not "[title]" in comment_body.lower():
                continue
    
            logging.info(f"Found title comment for {submission.id}: {comment.id}")
            title = comment_body[7:].strip()
            
            db[submission.id]["title"] = title

    def check_for_sub(self, submission: praw.Reddit.submission):
        for x in submission.title.split():          
            if (match := re.match(r"^[r]\/|^\/[r]\/", x)):
                title = x.replace(match.group(0), "").strip()
                logging.info(f"Found subreddit name of: {title}")
                
                return title
        if len(submission.title.split()) == 1:
            logging.info(f"Found subreddit name of: {submission.title}")
            return submission.title

    def is_ready(self, submission: praw.Reddit.submission):        
        for key in ("date", "title", "sub"):
            logging.debug(key)
            
            if not key in db[submission.id].keys():
                if key == "date" and "EMERGENCY" in db[submission.id].keys():
                    logging.info("Found post with no date that is scheduled for emergencies!")
                    continue
                return False
        return True

    def check_for_new_posts(self):
        global db

        for submission in self.sub.new(limit=15):
            announce = False
            
            logging.debug(f"Going through submission: {submission.title}")
            
            if not submission.link_flair_text in ("BOT READY", "EMERGENCY READY"):
                continue
            
            logging.info("Found BOT READY / EMERGENCY submission!")
            
            if not submission.id in db.keys():
                db[submission.id] = {}
                announce = True
                
            # Get the text of the post
            db[submission.id]["text"] = submission.selftext
            
            logging.debug(f"The text is: {db[submission.id]['text']}")
            
            if "IS_READY" in db[submission.id].keys():
                continue
            
            logging.info(submission.link_flair_text)
            
            if submission.link_flair_text != "EMERGENCY READY":
                self.search_for_dates(submission)
            else:
                db[submission.id]["EMERGENCY"] = None
            self.check_for_title(submission)
            if (sub := self.check_for_sub(submission)) != "":
                db[submission.id]["sub"] = sub
            
            if self.is_ready(submission):
                logging.info(f"Announcing {submission.id}")
                db[submission.id]["IS_READY"] = None
                announce = True
                
            if announce:                
                self.discord.new_post(db[submission.id], f"https://reddit.com{submission.permalink}")
            
    def create_schedule(self):        
        schedule = ScheduleBuilder()
        schedule.do_the_magic()
        text = schedule.finish_and_return()
        
        submission = self.reddit.submission(update_post_id)
        
        body = submission.selftext.split("=== STARTING BOT FIELD ===", 1)[0]
        submission.edit(body + text)

class PostHelper:
    def __init__(self, subreddit: str, reddit: praw.Reddit):
        self.reddit = reddit
        self.sub = reddit.subreddit(subreddit)
    
    def check_time(self):
        """Checks if the time is right to post the post. Also checks whether anything has been posted so far today"""
        now = datetime.datetime.now()
        
        for submission in self.sub.new(limit=3):
            if submission.removed:
                continue
            
            time_post = datetime.datetime.utcfromtimestamp(submission.created_utc)
            difference = now - time_post
            if (difference.total_seconds() / 3600) < 22:
                logging.info("Last post was less than 22 hours ago")
                return False
        
        if now.hour >= 12:
            return True
        
    def send_post(self):
        try:
            post_id = db["NEXT_POST"]
            
            if post_id not in db.keys():
                db.pop("NEXT_POST")
                logging.warning("Post wasn't in DB!")
                return
            
            post = db[post_id]

            try:
                devsub_post = self.reddit.submission(post_id)
                flair = devsub_post.link_flair_text 
            except prawcore.NotFound:
                flair = "404"
                logging.warning("Reddit returned 404 on request!")
                
            logging.debug(f"Flair is: {flair}")

            if not flair in ("BOT READY", "EMERGENCY"):
                logging.warning("Ghost in DB!")
                db.pop(db["NEXT_POST"])
                db.pop("NEXT_POST")
            
                return
        except (TypeError, KeyError):
            try:
                if "HAS_POSTED_ABOUT_NO_SUB" in db.keys() \
                and db["HAS_POSTED_ABOUT_NO_SUB"] == datetime.datetime.now().day:
                    logging.debug("Couldn't find next sub but already warned about it!")
                else:
                    raise KeyError
            except (TypeError, KeyError):
                logging.debug("Couldn't find next post!!!")
                discord = DiscordHelper(discord_webhook)
                discord.basic_message("Error Posting Post",
                                    "Couldn't find NEXT_POST in DB",
                                    Color.red)
                db["HAS_POSTED_ABOUT_NO_SUB"] = datetime.datetime.now().day
            finally:
                return
        
        title = "{} - /r/{}: {}".format(helpers.output_good_post_date_str(), post["sub"], post["title"]) # formatted strings fail on dict extractions
        
        if not DEV:
            submission = self.sub.submit(
                title = title,
                selftext = post["text"]
            )
        
            discord = DiscordHelper(discord_webhook)
            discord.basic_message("Posted To Subreddit!", f"https://reddit.com{submission.permalink}", Color.green)

            #devsub_post.flair.select("05cf3a30-3dc5-11e4-9983-12313b0ab8de")
    
            hostsub = self.reddit.subreddit(post["sub"])
            hostsub.submit(
                title = "Congratulations, /r/{}! You are Subreddit of the Day!".format(post["sub"]),
                url = f"https://reddit.com{submission.permalink}"
            )
        else:
            logging.debug("Script would have posted about: {}".format(post["sub"]))
            discord = DiscordHelper(discord_webhook)
            discord.basic_message("Script would have posted about: {}".format(post["sub"]), Color.red)
    
        db["LAST_POST_DAY"] = datetime.datetime.now().day
    
        db.pop(db["NEXT_POST"])
        db.pop("NEXT_POST")

class DiscordHelper:
    def __init__(self, webhook_url: str):
        # Extract from config.py
        self.webhook = DiscordWebhook(webhook_url)
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
        
        self.send_message()
        
    def new_post(self, data: dict, post_url: str):
        if "IS_READY" in data.keys():
            title = "New Post Ready"
            color = Color.green
        else:
            title = "New Draft Post"
            color = Color.gray
        
        sub = data["sub"] if "sub" in data.keys() else "UNKNOWN SUBREDDIT"
        post_title = data["title"] if "title" in data.keys() else "UNKNOWN TITLE"
        text = data["text"] if "text" in data.keys() else "UNKNOWN TEXT"
        
        self.embed = DiscordEmbed(
            title = f"/r/{sub}: {post_title}",
            description = f"{title}\n {text[:45]}\n [...]",
            color = color.value
        )
        
        self.embed.set_url(post_url)
        
        self.embed.set_author(name = "tomBOT", url = "https://github.com/tumGER/SubredditOfTheDay-Schedule-Bot", icon_url = "https://avatars.githubusercontent.com/u/25822956?v=4")
        
        if "date" in data.keys():
            dt = data["date"]
            date = "{}.{}.{}".format(dt["day"], dt["month"], dt["year"])
            
            self.embed.add_embed_field(name = "Date", value = date)
            
        self.embed.add_embed_field(name = "Status", value = "Emergency Post" if "EMERGENCY" in data.keys() else "Normal Post")
        
        self.webhook.add_embed(self.embed)
        logging.debug(self.webhook.execute(True))
        
    def send_message(self):
        self.webhook.add_embed(self.embed)
        logging.debug(self.webhook.execute(True))

class Color(enum.Enum):
    red = "ff0000"
    green = "00dd1f"
    gray = "a0a0a0"   

def main():      
    logging.root.handlers = []
    logging.basicConfig(
        level=logging.DEBUG if DEV else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )
    
    reddit = Reddit_Handler()
    reddit.tsrotd.check_for_new_posts()
    reddit.tsrotd.create_schedule()
    reddit.tsrotd.post_handling()
    
    if DEV:
        logging.debug("Sending DEV test post!")
        reddit.tsrotd.post.send_post()
    
    reddit.exit()

if __name__ == "__main__":
    print("Starting ...")
    print("Running in DEV mode" if DEV else "Running in PROD mode")
    main()