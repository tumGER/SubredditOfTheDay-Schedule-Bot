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