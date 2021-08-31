import datetime
import logging

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
    if date.month < now.month: # Date is next year when month provided is lower than the current one
        year += 1   
    return year

def parse_date(date: datetime.date):
    db_dt["day"] = date.day
    db_dt["month"] = date.month
    db_dt["year"] = find_year_by_datetime(date)