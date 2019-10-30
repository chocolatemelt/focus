#!/usr/bin/env python3
import datetime
import requests
import sys
import json

def map_invitees(res):
    """Maps invitees from a valid response body to their respective countries.

    Args:
        res - A response body as a dictionary.

    Returns:
        Dictionary mapping countries to its invitees.
    """
    country_mapping = {}
    for partner in res['partners']:
        partner_country = partner['country']
        if partner_country in country_mapping:
            country_mapping[partner_country].append(partner)
        else:
            country_mapping[partner_country] = [partner]

    return country_mapping

def get_valid_dates(available_dates):
    """Gets the valid dates for a two-day event from a list of available dates.

    A valid date is defined as any available date that has a consecutive available date, thus
    allowing for a two-day event.

    Args:
        available_dates - A list of available dates in ISO-8601 format.

    Returns:
        List of datetime objects of valid dates.
    """
    # get the equivalent datetime objects and sort them
    dates = list(map(lambda d: datetime.datetime.strptime(d, '%Y-%m-%d'), available_dates))
    dates.sort()

    # up until the last date, find consecutive and add it
    valid_dates = []
    for date in dates[:-1]:
        next_date = date + datetime.timedelta(days=1)
        if next_date in dates:
            valid_dates.append(date)
    return valid_dates

def organize_event(attendees):
    """Organizes a two-day event given the attendees' availability dates, returning the start date
    and its attendees, identified by their email address.

    The date returned will be the start date of the two-day period where the most partners will make
    it for both days in a row. In the case of multiple dates, organize_event returns the earliest
    date.

    Args:
        attendees - A list of attendees for a given event.

    Returns:
        Tuple of datetime object and attendees or None if no valid dates.
    """
    # map from available dates to the attendees that have it listed as an available date
    valid_date_mapping = {}
    for attendee in attendees:
        valid_dates = get_valid_dates(attendee['availableDates'])
        for date in valid_dates:
            if date in valid_date_mapping:
                valid_date_mapping[date].append(attendee['email'])
            else:
                valid_date_mapping[date] = [attendee['email']]

    # get the earliest date that has the highest number of attendees
    highest = 0
    ret = None
    for date in valid_date_mapping:
        count = len(valid_date_mapping[date])
        if count > highest:
            highest = count
            ret = date
    return (ret, valid_date_mapping[ret])

def construct(event, country):
    """Constructs a valid country dictionary, following the spec provided.

    {
        "attendeeCount": 1,
        "attendees": [
            "cbrenna@hs.com"
        ],
        "name": "Ireland",
        "startDate": "2017-04-29"
    }

    Args:
        event - A tuple containing the start date and its attendees.
        country - The country this event is for.

    Returns:
        Dictionary containing the relevant POST body as defined above.
    """
    ret = {}
    ret["attendeeCount"] = len(event[1])
    ret["attendees"] = event[1]
    ret["name"] = country
    ret["startDate"] = event[0].strftime('%Y-%m-%d')
    return ret

if __name__ == '__main__':
    # begin with getting a valid response from the candidacy test
    # normally, this key might be given in a configuration file, not hard-coded
    res = requests.get('')
    if res.status_code is not 200:
        print(f'Request failed with status code {res.status_code}:')
        print(res.text)
        sys.exit()
    body = res.json()

    # get the attendees per country
    country_mapping = map_invitees(body)
    # print(country_mapping)

    # for each country, find their respective dates and construct the req body format
    countries = []
    for country in country_mapping:
        countries.append(construct(organize_event(country_mapping[country]), country))

    # construct the final POST body...
    body = {'countries': countries}

    # ...and post it!
    res = requests.post(
        '',
        data = json.dumps(body),
        headers = {
            'Content-Type': 'application/json'
        }
    )
    if res.status_code is not 200:
        print(f'Request failed with status code {res.status_code}:')
        print(res.text)
        sys.exit()
    else:
        print('Posted successfully:')
        print(res.text)
        sys.exit()
