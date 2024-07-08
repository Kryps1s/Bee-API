"""
This lambda function will return all events in the calendar, with optional modifiers. 
"""
    # pylint: disable=R0801
import os
import csv
import re
import json
from datetime import datetime, timedelta
import requests

trello_boards = {
                "MEETING": os.environ['TRELLO_BOARD_MEETING'],
                "BEEKEEPING": os.environ['TRELLO_BOARD_BEEKEEPING'],
                "COLLECTIVE": os.environ['TRELLO_BOARD_COLLECTIVE']
            }

class Auth:
    """Auth class for storing token"""
    def __init__(self, token):
        self.token = token

    def set_token(self, token):
        """Set token"""
        self.token = token

auth = Auth("")

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

def fetch_events(url):
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
        raise TrelloAPIError("Trello API error: " + response.text)
    #remove cards with no due date
    cards = [card for card in response.json() if card['due'] is not None]
    return cards

def fetch_members():
    """Fetch all members from the organization"""
    #pylint: disable=R0801
    url = "https://api.trello.com/1/organizations/" + os.environ['TRELLO_ORGANIZATION'] + "/members"
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
    #filter invalid members from list of invalid members
    members = list(response.json())
    return members

def map_meeting_event(event, card, members):
    """Map trello card to meeting event"""
    event['__typename'] = "MeetingEvent"
    event['roles'] = []
    #check if label starting with MONTHLY is present
    for label in card['labels']:
        if label['name'].startswith("MONTHLY"):
            event['isMonthly'] = True
        if label['name'] == "ONLINE":
            event['location'] = "ONLINE"
        if label['name'] == "IN-PERSON":
            event['location'] = "IN-PERSON"
    desc = card['desc']
    # Find all emojis
    emojis = ["📣", "🔧", "✏️"]
    # Find next word starting with '@' symbol after each emoji
    for emoji in emojis:
        next_word = re.search(r'@(\w+)', desc[desc.find(emoji)+len(emoji):])
        if emoji == "📣":
            if next_word:
                event['roles'].append(process_role_line("@" + next_word.group(1), "Facilitator", members))
            else:
                event['roles'].append({'roleName': "Facilitator", 'user': None})
        elif emoji == "🔧":
            if next_word:
                event['roles'].append(process_role_line("@" + next_word.group(1), "Jockey", members))
            else:
                event['roles'].append({'roleName': "Jockey", 'user': None})
        elif emoji == "✏️":
            if next_word:
                event['roles'].append(process_role_line("@" + next_word.group(1), "Scribe", members))
            else:
                event['roles'].append({'roleName': "Scribe", 'user': None})
    #loop through description
    # for line in desc:
    #     if line.startswith("📣"):
            
    #         event['roles'].append(process_role_line(line, "Facilitator",members))
    #     elif line.startswith("🔧"):
    #         event['roles'].append(process_role_line(line, "Jockey",members))
    #     elif line.startswith("✏️"):
    #         event['roles'].append(process_role_line(line, "Scribe",members))
    # for line in desc:
    #     if line.startswith("📣"):
    #         event['roles'].append(process_role_line(line, "Facilitator",members))
    #     elif line.startswith("🔧"):
    #         event['roles'].append(process_role_line(line, "Jockey",members))
    #     elif line.startswith("✏️"):
    #         event['roles'].append(process_role_line(line, "Scribe",members))
    return event

def map_beekeeping_event(event, card):
    """Map trello card to beekeeping event"""
    event['__typename'] = "BeekeepingEvent"
    event['type'] = "BEEKEEPING"
    event['jobs'] = []
    event['hives'] = []
    event['roles'] = []
    event['link'] = None
    event['goal'] = None
    #try parsing {} enclosure in desc into json if first character is {
    if card['desc'].startswith("{") and is_valid_json(card['desc'].split("}")[0] + "}"):
        roles = json.loads(card['desc'].split("}")[0] + "}")
        #add roles to event
        event['roles'].append(roles)
    #loop through labels
    for label in card['labels']:
        #if label name starts with job: or hive:, add to event array
        if label['name'].startswith("job:"):
            event['jobs'].append(label['name'].split("job:")[1])
        elif label['name'].startswith("hive:"):
            event['hives'].append(label['name'].split("hive:")[1])
    return event

def process_role_line(line, role_name, members):
    """Process role line"""
    #find the string that starts with an @ and ends with a space
    #check if the line contains an @
    if "@" not in line:
        return {'roleName': role_name, 'user': None}
    username = line.split("@")[1].split(" ")[0]
    member = next((member for member in members if member['username'] == username),None)
    if member:
        return {'roleName': role_name, 'user': member}
    return {'roleName': role_name, 'user': {'username': username, 'fullName': username, 'id': 0}}

def get_hive_timelines(jobs):
    """map of inspections and link to previous inspection"""
    hive_arrays = {}
    for job in jobs:
        job_types = job['jobs']
        hive_ids = job['hives']
        job_details = {"eventId": job['eventId'], "description": job['notes']}
        if 'INSPECT' in job_types:
            for hive_id in hive_ids:
                if hive_id == 'ALL':
                    for hive_array in hive_arrays.values():
                        hive_array.append(job_details)
                elif hive_id not in hive_arrays:
                    hive_arrays[hive_id] = [job_details]
                else:
                    hive_arrays[hive_id].append(job_details)

    return hive_arrays

def get_goal(description):
    """Get goal from description"""
    #check if there is a goal
    if "➡️" not in description:
        return None
    goal = description.split("➡️")[1]
    #return None is goal is empty
    if goal == "":
        return None
    return goal

def map_card_to_event(members, event_type, cards):
    """Map trello card to event"""
    if cards is None or len(cards) == 0:
        return []
    events = []
    cards.sort(key=lambda x: x['due'])
    for card in cards:
        event = {}
        event['eventId'] = card['shortLink']
        event['type'] = event_type
        event['start'] = card['due']
        event['name'] = card['name']
        event['notes'] = card['desc']
        #map specific event fields
        if event_type == "BEEKEEPING":
            event = map_beekeeping_event(event, card)
            #add if there is at least one job
            if len(event['jobs']) > 0:
                events.append(event)
        elif event_type == "MEETING":
            event = map_meeting_event(event, card, members)
            events.append(event)
        else:
            event['__typename'] = "CollectiveEvent"
        if event_type == "BEEKEEPING" and 'INSPECT' in event['jobs']:
            #get hive timelines
            hive_timelines = get_hive_timelines(events)
            #loop through events with inspect job
            for event in events:
                if 'INSPECT' not in event['jobs'] or len(event['hives']) == 0:
                    continue
                hive = event['hives'][0]
                if hive in hive_timelines:
                    hive_timeline = hive_timelines[hive]
                    job_index = next((index for (index, d) in enumerate(hive_timeline) \
                                    if d["eventId"] == event['eventId']), None)
                    if job_index > 0:
                        event['link'] = hive_timeline[job_index-1]['eventId']
                        event['goal'] = get_goal(hive_timeline[job_index-1]['description'])
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
            filtered_events = []
            for event in item['events']:
                event_start = datetime.strptime(event['start'], "%Y-%m-%d").date()
                current_date = datetime.now().date()
                if future is True:
                    if event_start > current_date:
                        filtered_events.append(event)
                elif future is False:
                    if event_start < current_date:
                        filtered_events.append(event)
            if future is True:
                # Order by start date
                filtered_events.sort(key=lambda x: datetime.strptime(x['start'], "%Y-%m-%d"))
            elif future is False:
                filtered_events.sort(key=lambda x: datetime.strptime(x['start'], "%Y-%m-%d"), reverse=True)
            item['events'] = filtered_events
    else:
        for item in events:
            item['events'].sort(key=lambda x: datetime.strptime(x['start'], "%Y-%m-%d"))
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
        filtered_events = []
        for meeting_event in item['events']:
            if "isMonthly" in meeting_event and meeting_event["isMonthly"] is True:
                filtered_events.append(meeting_event)
        item['events'] = filtered_events
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
        members = fetch_members()
        if event_type is not None:
            for event_type in event['arguments']['type']:
                if event_type in trello_boards:
                    board_id = trello_boards[event_type]
                    events.append({'type': event_type,\
                                   'events': map_card_to_event(members, event_type, \
                                                               fetch_events(board_id))})
                else:
                    raise InvalidInputError("Invalid type: " + event_type)
        else: #if no type is specified, get all types
            for event_type, board_id in trello_boards.items():
                event['type'] = event_type
                events.append({'type': event_type,\
                               'events': map_card_to_event(members, event_type,\
                                                            fetch_events(board_id))})
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
        for event in events:
            event['start'] = datetime.strptime(event['start'], "%Y-%m-%d") + timedelta(hours=4)
            if event['type'] == "MEETING":
                event['start'] = event['start'].replace(hour=18, minute=0, second=0)
            event['start'] = event['start'].isoformat()
    return events
