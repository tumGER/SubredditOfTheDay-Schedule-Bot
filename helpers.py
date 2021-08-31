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
    