"""This lambda function will return all members of the trello 
organization that are valid options for user to link to their account."""

import os
import json
import requests

class TrelloAPIError(Exception):
    """Exception raised for errors in the Trello API"""

#the root trello user, and te buzzhub user are invalid members
invalid_members = ["585a7e82c8a3142c77cfb22e"]

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
    members = [user for user in response.json() if user['id'] not in invalid_members]
    return members
# pylint: disable=W0613
def lambda_handler(event, _):
    """Lambda handler"""
    try:
        members = fetch_members()
        #add __typename to each member
        for member in members:
            member['__typename'] = "TrelloMember"
        #print to cloudwatch logs
        print("members fetched: " + str(len(members)))
        print(members)
        return members
    except TrelloAPIError as err:
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(err)})
        }
