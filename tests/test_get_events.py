"""Test get_events function in lambda_handler.py"""
import os
import datetime
from collections import Counter
from unittest.mock import patch
import pytest
from lambdas.get_events import lambda_handler
from .utils import mock_beekeeping_board, mock_collective_board, mock_meeting_board

@pytest.fixture(name='event')
def fixture_event():
    """ Generates Appsync GraphQL Event"""
    return {
        "arguments": {}
    }

#test_get_events.py
@patch('lambdas.get_events.fetch_events')
def test_get_events(mock_fetch_events, event):
    """Test get_events function"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    result = lambda_handler(event, {})
    assert len(result) == 4

#test_get_events returns the limited number of events
@patch('lambdas.get_events.fetch_events')
def test_get_events_limit(mock_fetch_events, event):
    """Test get_events function with limit"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    event['arguments']['limit'] = 2
    # Call the function
    result = lambda_handler(event, {})
    # Check that for each type of event, the number of events is limited
    event_counts = Counter(event['type'] for event in result)
    #assert all the event types are under the limit
    for event_type in event_counts:
        assert event_counts[event_type] <= 2

#test_get_events returns the events in the future
@patch('lambdas.get_events.fetch_events')
def test_get_events_future(mock_fetch_events, event):
    """Test get_events function with future events"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    event['arguments']['future'] = True
    # Call the function
    result = lambda_handler(event, {})
    for item in result:
        #assert each event.start is in the future
        assert item['start'] > datetime.datetime.now().isoformat()

#test_get_events returns the events in the past
@patch('lambdas.get_events.fetch_events')
def test_get_events_past(mock_fetch_events, event):
    """Test get_events function with past events"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    event['arguments']['future'] = False
    event['arguments']['type'] = ["MEETING"]
    # Call the function
    result = lambda_handler(event, {})
    for item in result:
        #assert each event.start is in the past
        assert item['start'] < datetime.datetime.now().isoformat()


#test_get_events returns the events of selected type
@patch('lambdas.get_events.fetch_events')
def test_get_events_type(mock_fetch_events, event):
    """Test get_events function with type"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    event['arguments']['type'] = ['MEETING']
    # Call the function
    result = lambda_handler(event, {})
    # Check all events are of type MEETING
    for item in result:
        assert item['type'] == 'MEETING'

#test_get_events returns the events of selected job
@patch('lambdas.get_events.fetch_events')
def test_get_events_job(mock_fetch_events, event):
    """Test get_events function with job"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    event['arguments']['jobs'] = ['EQUIPMENT']
    event['arguments']['type'] = ['BEEKEEPING']
    # Call the function
    result = lambda_handler(event, {})
    # Check all events are of job BEEKEEPING
    for item in result:
        assert 'EQUIPMENT' in item['jobs']

#test get_events returns the events of selected hive
@patch('lambdas.get_events.fetch_events')
def test_get_events_hive(mock_fetch_events, event):
    """Test get_events function with hive"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    event['arguments']['hives'] = ['ROSE']
    event['arguments']['type'] = ['BEEKEEPING']
    # Call the function
    result = lambda_handler(event, {})
    # Check all events are of hive ROSE
    for item in result:
        assert 'ROSE' in item['hives'] or 'ALL' in item['hives']

#test date range
@patch('lambdas.get_events.fetch_events')
def test_get_events_date_range(mock_fetch_events, event):
    """Test get_events function with date range"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    #date range argument an array for start and end timestamps in format %Y-%m-%dT%H:%M:%S.%fZ
    event['arguments']['dateRange'] = ['2023-06-01T00:00:00.000Z', '2023-06-30T00:00:00.000Z']
    event['arguments']['type'] = ['MEETING']
    # Call the function
    result = lambda_handler(event, {})
    # Check all events are in the date range
    for item in result:
        assert item['start'] > '2023-06-01' and item['start'] < '2023-06-30'

#test date range dates are in correct order
@patch('lambdas.get_events.fetch_events')
def test_get_events_date_range_order(mock_fetch_events, event):
    """Test get_events function"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    #date range argument an array for start and end timestamps in format %Y-%m-%dT%H:%M:%S.%fZ
    event['arguments']['dateRange'] = ['2023-06-30T00:00:00.000Z', '2023-06-01T00:00:00.000Z']
    event['arguments']['type'] = ['MEETING']
    # Call the function
    try:
        lambda_handler(event, {})
    except ValueError as exception:
        assert str(exception) == 'Invalid date range'

#test date range dates are only one date
@patch('lambdas.get_events.fetch_events')
def test_get_events_date_range_one_date(mock_fetch_events, event):
    """Test get_events function"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    #date range argument an array for start and end timestamps in format %Y-%m-%dT%H:%M:%S.%fZ
    event['arguments']['dateRange'] = ['2023-06-30T00:00:00.000Z']
    event['arguments']['type'] = ['MEETING']
    # Call the function
    try:
        lambda_handler(event, {})
    except ValueError as exception:
        assert str(exception) == 'Invalid date range'

#test get all events with all arguments
@patch('lambdas.get_events.fetch_events')
def test_get_events_all_arguments(mock_fetch_events, event):
    """Test get_events function"""
    # Configure the mock behavior
    def side_effect(board_id):
        if board_id == os.environ['TRELLO_BOARD_MEETING']:
            return mock_meeting_board()
        if board_id == os.environ['TRELLO_BOARD_BEEKEEPING']:
            return mock_beekeeping_board()
        if board_id == os.environ['TRELLO_BOARD_COLLECTIVE']:
            return mock_collective_board()
        return []
    mock_fetch_events.side_effect = side_effect
    event['arguments']['dateRange'] = ['2023-06-01T00:00:00.000Z', '2023-06-30T00:00:00.000Z']
    event['arguments']['type'] = ['BEEKEEPING']
    event['arguments']['jobs'] = ['EQUIPMENT']
    event['arguments']['hives'] = ['ROSE']
    event['arguments']['limit'] = 1
    # Call the function
    result = lambda_handler(event, {})
    # Check all events are of job BEEKEEPING
    for item in result:
        assert 'EQUIPMENT' in item['jobs']
    # Check all events are of hive ROSE
    for item in result:
        assert 'ROSE' in item['hives'] or 'ALL' in item['hives']
    # Check all events are in the date range
    for item in result:
        assert item['start'] > '2023-06-01' and item['start'] < '2023-06-30'
        