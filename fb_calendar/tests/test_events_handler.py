import random
import json
import time

import mock
import tornado.testing

import app

randint = lambda: random.randint(0, 100000)

mock_events = [
    {'id': randint(),
     'page_id': randint(),
     'page_name': 'Page Name: ' + str(randint()),
     'name': 'Name: ' + str(randint()),
     'attending_count': randint(),
     'interested_count': randint(),
     'maybe_count': randint(),
     'start_time': int(time.time()) - randint(),
     'end_time': int(time.time()) + randint(),
     'picture_url': 'https://www.example.com/?q=' + str(randint()),
     'description': 'Description ' + str(randint()),
     'ticket_uri': 'https://www.example.com/ticket_uri/?q=' + str(randint()),
     'place': 'Place ' + str(randint())
     } for _ in range(5)
]

class TestEventsHandler(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return app.make_app()

    @mock.patch('event.select_events_for_user')
    def test_get_with_less_than_page_size_results(self, mock_select_events_for_user):
        mock_select_events_for_user.return_value = mock_events
        resp = self.fetch('/events?fbid=246&page_size=6')
        mock_select_events_for_user.assert_any_call(246, offset=0, limit=7)
        events = json.loads(resp.body)
        assert len(events.get('data')) == 5
        assert events.get('data') == mock_events

    @mock.patch('event.select_events_for_user')
    def test_get_with_page_size_results(self, mock_select_events_for_user):
        mock_select_events_for_user.return_value = mock_events
        resp = self.fetch('/events?fbid=246&page_size=5')
        mock_select_events_for_user.assert_any_call(246, offset=0, limit=6)
        events = json.loads(resp.body)
        assert len(events.get('data')) == 5
        assert events.get('data') == mock_events

    @mock.patch('event.select_events_for_user')
    def test_get_with_greater_than_page_size_results(self, mock_select_events_for_user):
        mock_select_events_for_user.return_value = mock_events
        resp = self.fetch('/events?fbid=246&page_size=4')
        mock_select_events_for_user.assert_any_call(246, offset=0, limit=5)
        events = json.loads(resp.body)
        assert len(events.get('data')) == 4
        assert events.get('data') == mock_events[0:4]

    @mock.patch('event.select_events_for_user')
    def test_next(self, mock_select_events_for_user):
        mock_select_events_for_user.return_value = mock_events
        resp = self.fetch('/events?fbid=246&page_size=2')
        mock_select_events_for_user.assert_any_call(246, offset=0, limit=3)
        events = json.loads(resp.body)
        assert len(events.get('data')) == 2
        assert events.get('data') == mock_events[0:2]
        assert events.get('next') == '/events?fbid=246&page=1&page_size=2'
        assert events.get('prev') == ''

    @mock.patch('event.select_events_for_user')
    def test_prev(self, mock_select_events_for_user):
        mock_select_events_for_user.return_value = mock_events
        resp = self.fetch('/events?fbid=246&page_size=2&page=1')
        mock_select_events_for_user.assert_any_call(246, offset=2, limit=3)
        events = json.loads(resp.body)
        assert len(events.get('data')) == 2
        assert events.get('data') == mock_events[0:2]
        assert events.get('prev') == '/events?fbid=246&page=0&page_size=2'
        assert events.get('next') == '/events?fbid=246&page=2&page_size=2'

    @mock.patch('event.select_friends_events_for_user')
    def test_friend_events(self, mock_select_friend_events):
        mock_select_friend_events.return_value = mock_events
        resp = self.fetch('/user/1/events/friends')
        mock_select_friend_events.assert_any_call(1, offset=0, limit=26)
        events = json.loads(resp.body)
        assert len(events.get('data')) == len(mock_events) 
        assert events.get('data') == mock_events
        assert events.get('prev') == ''
        assert events.get('next') == ''

    @mock.patch('handlers.event.Event')
    def test_put_events(self, mock_Event):
        # Set event ids from 0 increasing
        for i,ev in enumerate(mock_events):
            ev['id'] = i;
        mock_Event.select.side_effect = mock_events;
        resp = self.fetch('/events', method='PUT', body=json.dumps(
            [{'id': 0, 'name': 'my new event name'}, {'id': 1, 'hidden': 1}, {'id': 2, 'name': "my other new event name"}]
        ))
        # Get all the updates and really apply them to mock_events so we can then check for changes
        for call in mock_Event.update.call_args_list:
            id = call[0][0]["id"]
            event = mock_events[id]
            for k,v in call[0][0].iteritems():
                if k != "id":
                    event[k] = v
        # Verify that indeed the events have been updated
        assert mock_events[0]['name'] == 'my new event name'
        assert mock_events[1]['hidden'] == 1
        assert mock_events[2]['name'] == 'my other new event name'
