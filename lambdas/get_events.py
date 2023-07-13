"""
This lambda function will return all events in the calendar, with optional modifiers. 
"""
    # pylint: disable=R0801
import os
import json
from datetime import datetime
import requests

trello_boards = {
                "MEETING": os.environ['TRELLO_BOARD_MEETING'],
                "BEEKEEPING": os.environ['TRELLO_BOARD_BEEKEEPING'],
                "COLLECTIVE": os.environ['TRELLO_BOARD_COLLECTIVE']
            }

class TrelloAPIError(Exception):
    """Exception raised for errors in the Trello API"""
class InvalidInputError(Exception):
    """Exception raised for invalid input"""

def is_valid_json(json_str):
    """Check if string is valid json"""
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False

def fetch_events(board_id):
    """Fetch all cards from a board"""
    url = "https://api.trello.com/1/boards/" + board_id + "/cards"
    headers = {
    "Accept": "application/json"
    }
    query = {
    'key': os.environ['TRELLO_KEY'],
    'token': os.environ['TRELLO_TOKEN']
    }
    response = requests.request(
    "GET",
    url,
    headers=headers,
    params=query,
    timeout=30
    )
    if response.ok is False:
        raise TrelloAPIError("Trello API error: " + response['error'])
    #remove cards with no due date
    cards = [card for card in response.json() if card['due'] is not None]
    return cards


def map_card_to_event(event_type, cards):
    """Map trello card to event"""
    events = []
    for card in cards:
        event = {}
        event['eventId'] = card['shortLink']
        event['type'] = event_type
        event['start'] = card['due']
        #map specific event fields
        if event_type == "BEEKEEPING":
            event['jobs'] = []
            event['hives'] = []
            event['roles'] = []
            #try parsing {} enclosure in desc into json if first character is {
            if card['desc'].startswith("{") and is_valid_json(card['desc'].split("}")[0] + "}"):
                roles = json.loads(card['desc'].split("}")[0] + "}")
                #add roles to event
                event['roles'].append(roles)
            event['type'] = event_type
            #loop through labels
            for label in card['labels']:
                #if label name starts with job or hive, add to event array
                if label['name'].startswith("job"):
                    event['jobs'].append(label['name'].split("job:")[1])
                elif label['name'].startswith("hive"):
                    event['hives'].append(label['name'].split("hive:")[1])
            #add if there is at least one job
            if len(event['jobs']) > 0:
                events.append(event)
        elif event_type == "MEETING":
            #check if label starting with MONTHLY is present
            for label in card['labels']:
                if label['name'].startswith("MONTHLY"):
                    event['isMonthly'] = True
                if label['name'] == "ONLINE":
                    event['location'] = "ONLINE"
                if label['name'] == "IN-PERSON":
                    event['location'] = "IN-PERSON"
            events.append(event)
    return events

def filter_events_by_date_range(events, date_range):
    """Filter events by date range"""
    if date_range is not None:
        if (len(date_range) != 2 or
        datetime.strptime(date_range[0], "%Y-%m-%dT%H:%M:%S.%fZ") > \
            datetime.strptime(date_range[1], "%Y-%m-%dT%H:%M:%S.%fZ")):
            raise ValueError("Invalid date range")
        filtered_events = []
        for event in events:
            if datetime.strptime(event['start'], "%Y-%m-%dT%H:%M:%S.%fZ") > \
                datetime.strptime(date_range[0], "%Y-%m-%dT%H:%M:%S.%fZ") and \
                    datetime.strptime(event['start'], "%Y-%m-%dT%H:%M:%S.%fZ") < \
                        datetime.strptime(date_range[1], "%Y-%m-%dT%H:%M:%S.%fZ"):
                filtered_events.append(event)
        events = filtered_events
    return events

def filter_events_by_future_and_order(events, future):
    """Filter events by future"""
    if future is not None:
        for item in events:
            for event in item['events']:
                if future is True:
                    if datetime.strptime(event['start'], "%Y-%m-%dT%H:%M:%S.%fZ") < datetime.now():
                        item['events'].remove(event)
                elif future is False:
                    if datetime.strptime(event['start'], "%Y-%m-%dT%H:%M:%S.%fZ") > datetime.now():
                        item['events'].remove(event)
            if future is True:
                #order by start date
                item['events'].sort(key=lambda x: x['start'])
            elif future is False:
                item['events'].sort(key=lambda x: x['start'], reverse=True)
    else:
        for item in events:
            item['events'].sort(key=lambda x: x['start'])
    return events

def filter_events_by_beekeeping(item, hives, jobs):
    """Filter beekeeping events by hives and jobs"""
    if hives is not None:
        filtered_events = []
        for beekeeping_event in item['events']:
            #if no union between hive and beekeeping_event, remove beekeeping_event
            #check if array contains ALL
            if len(set(hives).intersection(set(beekeeping_event["hives"]))) > 0 or \
                "ALL" in beekeeping_event["hives"]:
                filtered_events.append(beekeeping_event)
        item['events'] = filtered_events
    if jobs is not None:
        filtered_events = []
        for beekeeping_event in item['events']:
            #if no union between hive and beekeeping_event, remove beekeeping_event
            if len(set(jobs).intersection(set(beekeeping_event["jobs"]))) > 0:
                filtered_events.append(beekeeping_event)
        item['events'] = filtered_events
    return item

def filter_events_by_meeting(item, is_monthly):
    """Filter meeting events by is_monthly"""
    if is_monthly is True:
        for meeting_event in item['events']:
            if meeting_event["isMonthly"] != is_monthly:
                item['events'].remove(meeting_event)
    return item

def lambda_handler(event, _):
    """
    wrapper around the google calendar api. 
    event : the event object from the GraphQL query
    arguments : the arguments object from the GraphQL query
        type : string, from the GraphQL type enum 
        limit : int, the number of items to return of each type
        future : boolean, if true, only return events that have not ended, if false, 
            only return events that have ended, if null, return all events
		dateRange: array of start and end timestamp, if one index then it is the start and end time
		isMonthly: Boolean, for meetings events to denote the monthly checkin
		job: [BeekeepingJob], beekeeping job to filter by
		hive: [String] hive to filter by
    """
    events = []
    if 'arguments' in event:
        arguments = event.get('arguments', {})
        event_type = arguments.get('type')
        limit = arguments.get('limit')
        future = arguments.get('future')
        date_range = arguments.get('dateRange')
        is_monthly = arguments.get('isMonthly')
        jobs = arguments.get('jobs')
        hives = arguments.get('hives')

        if event_type is not None:
            for event_type in event['arguments']['type']:
                if event_type in trello_boards:
                    board_id = trello_boards[event_type]
                    events.append({'type': event_type,\
                                   'events': map_card_to_event(event_type, fetch_events(board_id))})
                else:
                    raise InvalidInputError("Invalid type: " + event_type)
        else: #if no type is specified, get all types
            for event_type, board_id in trello_boards.items():
                event['type'] = event_type
                events.append({'type': event_type,\
                               'events': map_card_to_event(event_type, fetch_events(board_id))})
        #type specific filters
        for item in events:
            if item["type"] == "BEEKEEPING":
                filter_events_by_beekeeping(item, hives, jobs)
            if item["type"] == "MEETING":
                filter_events_by_meeting(item, is_monthly)
        events = filter_events_by_future_and_order(events, future)
        if limit is not None:
            for item in events:
                item['events'] = item['events'][:limit]
        #flatten events
        events = [event for item in events for event in item['events']]
        events = filter_events_by_date_range(events, date_range)
    return events