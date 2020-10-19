import os
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

from ticktick import TickTick
from pytz import timezone

UTC = timezone('utc')
##################################################
########       CONNECTING TO NOTION       ########
##################################################
def connect_ticktick(username, password):
    client = TickTick(username, password)
    client.fetch()
    return client


#################################################
########       ADDING TO TICKTICK        ########
#################################################
# simple function to combine dates and times when needed
def clean_datetime(dt, timezone=None):
    # if time was added, combine it
    if dt["time"]:
        return False, datetime.combine(dt["date"], dt["time"].replace(tzinfo=timezone))
    # if not, return just the date
    elif dt['date']:
        return True, datetime(dt['date'].year, dt['date'].month, dt['date'].day, tzinfo=timezone)
    else:
        return True, None

def serialize_datetime(date):
    string = date.astimezone(UTC).isoformat()
    string = string[:-6] + ".000" + string[-6:-3] + string[-2:]
    return string


def add_notion(client, params, recur):
    # parse through recur data
    tz = timezone(client.guess_timezone()) #timezone(recur["timezone"])
    _, start_date = clean_datetime(recur["start_date"], tz)
    _, end_date = clean_datetime(recur["end_date"], tz)
    count = recur["count"]
    types = recur["types"]
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
        # combine date and times
        if isinstance(v, dict):
            isAllDay, params[k] = clean_datetime(v, tz)

    # Set up iterative variables
    if types in ["dates_both", "dates_mix"]:
        params['dueDate'] = start_date
    if types in ["dates_mix", "number"]:
        ccount = 0

    still_going = True
    while still_going:
        # if that's not a day we're supposed to add, skip (and check if we should stop)
        if (
            types in ["dates_both", "dates_mix"]
            and params['dueDate'].weekday() not in days
        ):
            params['dueDate'] += timedelta(days=1)
            if types == "dates_both" and params['dueDate'] > end_date:
                still_going = False
            continue

        # add it
        client.add(params['title'], list_name=params['list'],
                    extra_kwargs={'priority': params['priority'],
                                    'tags': params['tags'],
                                    'dueDate': serialize_datetime(params['dueDate']), 'isAllDay': isAllDay})
        print(isAllDay, serialize_datetime(params['dueDate']))

        # increment date and count (and check if we should stop)
        if types in ["dates_both", "dates_mix"]:
            params['dueDate'] += timedelta(days=1)
        if types == "dates_both" and params['dueDate'] > end_date:
            still_going = False
        if types in ["dates_mix", "number"]:
            ccount += 1
            if ccount >= count:
                still_going = False
