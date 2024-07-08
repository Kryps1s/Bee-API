"""update a trello card with the new event information"""
import json
import os
import requests

#an enum of supported update keys
UPDATE_KEYS = ['name', 'desc', 'idMembers', 'closed', 'due', 'idList', 'idLabels', 'idBoard']

def lambda_handler(event, _):
    """update a trello card with the new event information"""
    #get the trello client
    #get the card id, name, and description from the event
    card_id = event['arguments']['eventId']
    updates = event['arguments']['updates']
    #check that updates is a dict, and that it only contains valid keys
    if not isinstance(updates, dict):
        raise TypeError("updates must be a dict")
    for key in updates:
        if key not in UPDATE_KEYS:
            raise ValueError("invalid key: " + key)
    #pylint: disable=R0801
    url = "https://api.trello.com/1/cards/" + card_id
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
    json=updates,
    timeout=30
    )
    if response.ok is False:
        raise ValueError("Trello API error: " + response.text)
    response = json.loads(response.text)
    updates['version'] = response['version']
    updates['comment'] = "Updated event information"
    response = requests.request(
    "PATCH",
    url,
    headers=headers,
    data=updates,
    timeout=30
    )
    if response.ok is False:
        raise ValueError("Trello API error: " + response.text)
    return response.json()
