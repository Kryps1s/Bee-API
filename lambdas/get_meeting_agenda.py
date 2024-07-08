""" get the current agenda for the weekly meeting """
import csv
import os
import requests

def get_trello_board(board):
    """get trello board"""
    req_url = "https://api.trello.com/1/boards/" + board + "/cards"
    req_header = {
    "Accept": "application/json"
    }
    query = {
    'key': os.environ['TRELLO_KEY'],
    'token': os.environ['TRELLO_TOKEN']
    }
    # pylint: disable=R0801
    response = requests.request(
    "GET",
    headers=req_header,
    params=query,
    timeout=35,
    url=req_url
    )
    if response.ok is False:
        raise ValueError("Trello API error: " + response.text)
    return response.json()

def sort_cards(cards,board):
    """sort cards into unassigned, in progress, and completed"""
    #if board is BEEKEEPING get the list ids for the unassigned, in progress, and completed lists
    if board == 'BEEKEEPING':
        unassigned_id = os.environ['BEEKEEPING_LIST_UNASSIGNED']
        in_progress_id = os.environ['BEEKEEPING_LIST_IN_PROGRESS']
        completed_id = os.environ['BEEKEEPING_LIST_COMPLETED']
    #if board is COLLECTIVE get the list ids for the unassigned, in progress, and completed lists
    elif board == 'COLLECTIVE':
        unassigned_id = os.environ['COLLECTIVE_LIST_UNASSIGNED']
        in_progress_id = os.environ['COLLECTIVE_LIST_IN_PROGRESS']
        completed_id = os.environ['COLLECTIVE_LIST_COMPLETED']
        #else raise an error
    else:
        raise ValueError("Board must be BEEKEEPING or COLLECTIVE")
    #get the unassigned, in progress, and completed cards
    unassigned_cards = []
    in_progress_cards = []
    completed_cards = []
    for card in cards:
        #remove every in card but its name, and list id, idMembers, labels, due, and short link
        card = {'name': card['name'], 'idList': card['idList'], \
                'participants': card['idMembers'], 'labels': card['labels'], \
                    'start': card['due'], 'eventId': card['shortLink']}
        #convert the labels to a list of string names of the labels
        card['labels'] = [label['name'] for label in card['labels']]
        if card['idList'] == unassigned_id:
            unassigned_cards.append(card)
        elif card['idList'] == in_progress_id:
            in_progress_cards.append(card)
        elif card['idList'] == completed_id:
            completed_cards.append(card)
    #sort the unassigned, in progress, and completed cards by due date,
    # then name. put cards with no due date at the end
    unassigned_cards = sorted(unassigned_cards,\
                              key=lambda card: (card['start'] is None, card['start'], card['name']))
    in_progress_cards = sorted(in_progress_cards,\
                              key=lambda card: (card['start'] is None, card['start'], card['name']))
    completed_cards = sorted(completed_cards,\
                              key=lambda card: (card['start'] is None, card['start'], card['name']))
    #return the unassigned, in progress, and completed cards as one dict of lists
    return {'unassigned': unassigned_cards,\
            'inProgress': in_progress_cards,\
            'completed': completed_cards}

def lambda_handler(event, _):
    """get the current agenda for the weekly meeting"""
    #get the unassigned, in progress, and completed cards
    #get the beekeeping and collective boards
    print(event)
    beekeeping_cards= get_trello_board(os.environ['TRELLO_BOARD_BEEKEEPING'])
    collective_cards = get_trello_board(os.environ['TRELLO_BOARD_COLLECTIVE'])
    #get the unassigned, in progress, and completed cards for each board
    beekeeping_cards = sort_cards(beekeeping_cards, 'BEEKEEPING')
    collective_cards = sort_cards(collective_cards, 'COLLECTIVE')
    #return the unassigned, in progress, and completed cards for each board
    return {'BEEKEEPING': beekeeping_cards, 'COLLECTIVE': collective_cards}
