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

import datetime
import logging
import dateparser.search

def check_if_date_valid(date: datetime.datetime):
    """Checks whether the datetime has at least a valid day and month

    Args:
        date (datetime.datetime): The datetime object

    Returns:
        Bool: True or False
    """    
    if None in (date.day, date.month):
        logging.warning("Day / Month wasn't valid!")
        return False
    return True
    
def find_year_by_datetime(date: datetime.datetime):
    """Returns fitting year based on datetime object

    Args:
        date (datetime.datetime): datetime

    Returns:
        int: year
    """
    now = datetime.datetime.now()
    
    if (year := date.year) == None: # If no year was provided, year is likely this year
        year = now.year
    if date.month == 1 and now.month == 12: # Date is next year when month provided is lower than the current one
        year += 1
    return year

def parse_date_from_string(string: str):
    """Tries to find dates in a longer string

    Args:
        string (str): String to search on

    Returns:
        None or Datetime: Depending on success 
    """
    data = dateparser.search.search_dates(string)
    
    if data == None:
        return None
    
    if len(data) > 1:
        logging.error("Amount of dates was more than one - For some reason ...")
        
    return data[0][1]

def parse_date(date: datetime.date):
    """Parses dates from a datetime into a dictionary

    Args:
        date (datetime.date): Date

    Returns:
        dict: Dictionary with dates as strings
    """
    db_dt = {}
    
    db_dt["day"] = date.day
    db_dt["month"] = date.month
    db_dt["year"] = find_year_by_datetime(date)
    
    return db_dt

def output_good_post_date_str():
    """Returns a formatted date in the style of the subreddit titles

    Returns:
        str: Formatted datestring
    """
    date = datetime.datetime.now()
    
    endings = {
        1: "st",
        2: "nd",
        3: "rd"
    }
    
    ending = endings[date.day] if date.day in endings.keys() else "th" # Some Match Casing till actual match casing arrives in Python 3.10
    
    month = date.strftime("%B")
    str_date = f"{month} {str(date.day)}{ending}, {str(date.year)}"
    
    return str_date