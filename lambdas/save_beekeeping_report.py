"""Save a job report to a trello card"""
import datetime
import os
import requests

def lambda_handler(event, _):
    """Lambda handler"""
    #validate event
    try:
        validate_event(event)
    except KeyError as err:
        raise ValueError("missing field: " + str(err)) from err
    except ValueError as err:
        raise ValueError(str(err)) from err
    #get card id from event
    card_id = event['arguments']['eventId']
    #get report from event
    report = event['arguments']['report']
    #get the participants from event
    participants = event['arguments']['participants']
    #get next inspection details and validate, if any
    if event['arguments']['nextInspection'] is not None:
        #validate inspection
        valid = validate_inspection(event['arguments']['nextInspection'])
        if valid is not True:
            raise ValueError(valid)
    #validate report
    if not validate_report(report):
        raise ValueError("invalid report")
    #validate participants
    valid = validate_participants(participants)
    if valid is not True:
        raise ValueError(valid)
    #fetch card
    card = fetch_card(card_id)
    #add report to card
    card['desc'] = requests.utils.unquote(report)
    #add participants to card
    card['idMembers'] = participants
    #mark card as complete
    card['dueComplete'] = True
    #move card to Completed column
    card['idList'] = os.environ['BEEKEEPING_LIST_COMPLETED']
    #update card
    card = update_card(card)
    #create next event
    if event['arguments']['nextInspection'] is not None:
        if event['arguments']['goal'] is not None:
            card['desc'] = event['arguments']['goal']
        card['due'] = event['arguments']['nextInspection']
        #get the label with the hive name and add it to the card
        hive = 'UNKNOWN HIVE'
        for label in card['labels']:
            #if label name contains hive:
            if label['name'].find('hive:') != -1:
                hive = label['name'].replace('hive:', '')
                break
        #get card name, full or partial based on inspection full, then display hive name
        if event['arguments']['full']:
            card_name = 'Full Inspection: ' + hive
        else:
            card_name = 'Partial Inspection: ' + hive
        card['name'] = card_name
        create_next_inspection(card)
        return {"message": "successfully saved report and created next inspection"}
    return {"message": "successfully saved report"}

def fetch_card(card_id):
    """fetch card from trello"""
    url = "https://api.trello.com/1/cards/" + card_id
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
        raise ValueError("Trello API error: " + response.text)
    return response.json()

def update_card(card):
    """update card in trello"""
    url = "https://api.trello.com/1/cards/" + card['shortLink']
    headers = {
    "Accept": "application/json"
    }
    query = {
    'key': os.environ['TRELLO_KEY'],
    'token': os.environ['TRELLO_TOKEN'],
    }
    response = requests.request(
    "PUT",
    url,
    headers=headers,
    params=query,
    json=card,
    timeout=30
    )
    if response.ok is False:
        raise ValueError("Trello API error: " + response.text)
    return response.json()

def validate_report(report):
    """Validate report"""
    #check if report is a string
    if not isinstance(report, str):
        return False
    #check if report is empty
    if not report:
        return False
    return True

def validate_participants(participants):
    """Validate participants"""
    #check if participants is an array
    if not isinstance(participants, list):
        return "invalid participants"
    #check if participants is empty
    if not participants:
        return "there must be at least one attendee"
    #check if participants is an array of strings
    for item in participants:
        if not isinstance(item, str):
            return "invalid participants"
    return True

def validate_event(event):
    """validate event"""
    #check if event is a dict
    if not isinstance(event, dict):
        return False
    #check if arguments is a dict
    if not isinstance(event['arguments'], dict):
        return False
    #check if eventId is a string
    if not isinstance(event['arguments']['eventId'], str):
        return False
    #check if report is a string
    if not isinstance(event['arguments']['report'], str):
        return False
    #check if participants is a list
    if not isinstance(event['arguments']['participants'], list):
        return False
    return True

def validate_inspection(inspection):
    """validate inspection"""
    valid = True
    #check if date is a string
    if not isinstance(inspection, str):
        valid = False
    #check if date is empty
    if not inspection:
        valid = "date for next inspection cannot be empty"
    #check if date is not in the past
    today = datetime.date.today()
    year = int(inspection[0:4])
    month = int(inspection[5:7])
    day = int(inspection[8:10])
    date = datetime.date(year, month, day)
    if date < today:
        valid = "next inspection date must be greater than today"
    #check if date is in the format YYYY-MM-DD
    if len(inspection) != 10:
        valid = False
    if inspection[4] != '-' or inspection[7] != '-':
        valid = False
    return valid

def create_next_inspection(inspection):
    """create card in trello"""
    url = "https://api.trello.com/1/cards"
    headers = {
    "Accept": "application/json"
    }
    query = {
    'key': os.environ['TRELLO_KEY'],
    'token': os.environ['TRELLO_TOKEN'],
    'idList': os.environ['BEEKEEPING_LIST_UNASSIGNED'],
    'dueComplete': False,
    'idLabels': inspection['idLabels'],
    'due': inspection['due'] + 'T12:00:00.000Z',
    'pos': 'top',
    'desc': inspection['desc'],
    'name': inspection['name'],
    'idMembers': [],
    }
    response = requests.request(
    "POST",
    url,
    headers=headers,
    params=query,
    timeout=30
    )
    if response.ok is False:
        raise ValueError("Trello API error: " + response.text)
    return response.json()
