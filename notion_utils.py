import os
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

from notion.client import NotionClient


##################################################
########       CONNECTING TO NOTION       ########
##################################################
def connect_notion(url, token):
    if token == "":
        token = os.environ.get("BOT_TOKEN")
    client = NotionClient(token_v2=token)
    view = client.get_collection_view(url)
    return client, view.collection


#################################################
########        ADDING TO NOTION         ########
#################################################
# simple function to combine dates and times when needed
def clean_datetime(dt):
    # if time was added, combine it
    if dt["time"]:
        return datetime.combine(dt["date"], dt["time"].replace(tzinfo=None))
    # if not, return just the date
    else:
        return dt["date"]


def ensure_datetime(d):
    """Takes a date or a datetime as input, outputs a datetime."""
    if isinstance(d, datetime):
        return d
    return datetime(d.year, d.month, d.day)


def add_notion(collection, params, recur):
    print(params)
    # parse through recur data
    start_date = clean_datetime(recur["start_date"])
    end_date = clean_datetime(recur["end_date"])
    count = recur["count"]
    types = recur["types"]
    date_options = recur["date_options"]
    days = ["M", "Tu", "W", "Th", "F", "Sat", "Sun"]
    days = []
    if recur["M"]:
        days.append(0)
    if recur["Tu"]:
        days.append(1)
    if recur["W"]:
        days.append(2)
    if recur["Th"]:
        days.append(3)
    if recur["F"]:
        days.append(4)
    if recur["Sat"]:
        days.append(5)
    if recur["Sun"]:
        days.append(6)

    # clean out params given
    params.pop("csrf_token")
    for k, v in params.items():
        # make numbers floats
        if isinstance(v, Decimal):
            params[k] = float(v)
        # combine date and times
        if isinstance(v, dict):
            params[k] = clean_datetime(v)

    # Set up iterative variables
    if types in ["dates_both", "dates_mix"]:
        params[date_options] = start_date
    if types in ["dates_mix", "number"]:
        ccount = 0

    print(params)
    still_going = True
    while still_going:
        # if that's not a day we're supposed to add, skip (and check if we should stop)
        if (
            types in ["dates_both", "dates_mix"]
            and params[date_options].weekday() not in days
        ):
            params[date_options] += timedelta(days=1)
            if types == "dates_both" and ensure_datetime(
                params[date_options]
            ) > ensure_datetime(end_date):
                still_going = False
            continue

        # add it
        collection.add_row(**params)

        # increment date and count (and check if we should stop)
        if types in ["dates_both", "dates_mix"]:
            params[date_options] += timedelta(days=1)
        if types == "dates_both" and ensure_datetime(
            params[date_options]
        ) > ensure_datetime(end_date):
            still_going = False
        if types in ["dates_mix", "number"]:
            ccount += 1
            if ccount >= count:
                still_going = False
