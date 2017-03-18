from __future__ import absolute_import

import json
import logging

import tornado.web
import tornado.gen

import event
from event import UserEvent
from event import Event
from handlers.base import BaseHandler


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserEvents(BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        """
        This endpoint is intended to provide a ranking of events as a list view. The corresponding detail view should be
        called Event. At the moment the default ranking is just by the number of people interested in the event. We
        will soon change this to a more sophisticated metric, but probably not for the MVP.

        :param int fbid: The user's Facebook ID
        :param int page: Which page of results should be returned.
        :param int page_size: The number of results to return per-page.
        :returns: A list of events by the default ranking as well as standard pagination parameters.

          .. code-block:: JSON

              {
                "data": [
                    {
                        "id": "int",
                        "page_id": "int",
                        "page_name": "str",
                        "name": "str",
                        "attending_count": "int",
                        "interested_count": "int",
                        "noreply_count": "int",
                        "maybe_count": "int",
                        "start_time": "int",
                        "end_time": "int",
                        "picture_url": "str",
                        "description": "str",
                        "ticket_uri": "str",
                        "place": "str"
                    }, 
                ],
                "next": "/events?page=2&page_size=25&fbid=123",
                "prev": "/events?page=0&page_size=25&fbid=123"
              }
        """
        fbid = int(self.get_argument('fbid'))
        page = int(self.get_argument('page', '0'))
        limit = int(self.get_argument('page_size', '25'))

        logger.info("Getting events for just this user...");
        events = [e for e in event.select_events_for_user(fbid, offset=page*limit, limit=limit+1)]
        logger.info("Got {} events".format(len(events)))

        next, prev = self.get_next_and_prev(page, limit, events)

        self.write({
            'data': events[0:limit],
            'next': next,
            'prev': prev
        })

    @tornado.gen.coroutine
    def post(self, s_user_id, s_event_id):
        """
        This endpoint is intended to save an event to the user's personal feed (the table user_event).
            If the event already exists, only the updated_at field is modified.

        :param string s_user_id: The user's Facebook ID
        :param string s_event_id: The ID of the event.
        :returns: A pair of user_id, event_id.
        """
        user_id = int(s_user_id)
        event_id = int(s_event_id)

        user_event = event.select_user_event(user_id, event_id)
        if user_event is None:
            UserEvent.create(event_id=event_id, fb_user_id=user_id)
        else:
            event.update_user_event(user_id, event_id)

        self.write({
            'user_id': user_id,
            'event_id': event_id,
        })

    @tornado.gen.coroutine
    def put(self):
        """
        This endpoint is intended to update fields on a list of events. The updates are specified
            in the PUT body as below. id is required for each update.

          .. code-block:: JSON
          
              [{"id": 0, "name": "my new event name"}, {"id": 1, "hidden": 1}, {"id": 2, "name": "my other new event name"}]

        """
        updates = json.loads(self.request.body)
        for update in updates:
            Event.update(update)

class BigEvents(BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        """
        This endpoint is intended to provide a ranking of events as a list view. The corresponding detail view should be
        called Event. These events will be ordered by the number of people interested in them, and do not correspond
        to the user's liked pages.

        :param int page: Which page of results should be returned.
        :param int page_size: The number of results to return per-page.
        :returns: A list of events ranked by the sheer volume of people interested in them

          .. code-block:: JSON

              {
                "data": [
                    {
                        "id": "int",
                        "page_id": "int",
                        "page_name": "str",
                        "name": "str",
                        "attending_count": "int",
                        "interested_count": "int",
                        "noreply_count": "int",
                        "maybe_count": "int",
                        "start_time": "int",
                        "end_time": "int",
                        "picture_url": "str",
                        "description": "str",
                        "ticket_uri": "str",
                        "place": "str"
                    },
                ],
                "next": "/events?page=2&page_size=25",
                "prev": "/events?page=0&page_size=25"
              }
        """
        page = int(self.get_argument('page', '0'))
        limit = int(self.get_argument('page_size', '25'))

        logger.info("Getting events by interested count...");
        events = [e for e in event.select_events_by_interested_count(offset=page*limit, limit=limit+1)]
        logger.info("Got {} events".format(len(events)))

        next, prev = self.get_next_and_prev(page, limit, events)

        self.write({
            'data': events[0:limit],
            'next': next,
            'prev': prev
        })


class CoolEvents(BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        """
        This endpoint is intended to provide a ranking of events as a list view. The corresponding detail view should be
        called Event. These events are ranked by the ratio of those "going to" the event to those that have not yet
        replied to their invitation.

        :param int page: Which page of results should be returned.
        :param int page_size: The number of results to return per-page.
        :returns: A list of events by the default ranking as well as standard pagination parameters.

          .. code-block:: JSON

              {
                "data": [
                    {
                        "id": "int",
                        "page_id": "int",
                        "page_name": "str",
                        "name": "str",
                        "attending_count": "int",
                        "interested_count": "int",
                        "noreply_count": "int",
                        "maybe_count": "int",
                        "start_time": "int",
                        "end_time": "int",
                        "picture_url": "str",
                        "description": "str",
                        "ticket_uri": "str",
                        "place": "str"
                    }, 
                ],
                "next": "/events?page=2&page_size=25",
                "prev": "/events?page=0&page_size=25"
              }
        """
        page = int(self.get_argument('page', '0'))
        limit = int(self.get_argument('page_size', '25'))

        logger.info("Getting events by attendance ratio...");
        events = [e for e in event.select_events_by_attendance_ratio(offset=page*limit, limit=limit+1)]
        logger.info("Got {} events".format(len(events)))

        next, prev = self.get_next_and_prev(page, limit, events)

        self.write({
            'data': events[0:limit],
            'next': next,
            'prev': prev
        })

class FriendEvents(BaseHandler):
    
    @tornado.gen.coroutine
    def get(self, fbid):
        """
        This endpoint requires
            1. A user's friends have been stored (through the friend_scraper process) and 
            2. Those friends have had their pages/events pulled (through the event_scraper process)

        After that happens we count the number of friends that will potentially have an event 
            presented to them in their FB NewsFeed. We order by that. This endpoint is pretty 
            heavy as it takes three left joins. We may need to reassess the performance of it later.

        :param int fbid: The user's Facebook ID
        :param int page: Which page of results should be returned.
        :param int page_size: The number of results to return per-page.
        :returns: A list of events by the default ranking as well as standard pagination parameters.

          .. code-block:: JSON

              {
                "data": [
                    {
                        "id": "int",
                        "page_id": "int",
                        "page_name": "str",
                        "name": "str",
                        "attending_count": "int",
                        "interested_count": "int",
                        "noreply_count": "int",
                        "maybe_count": "int",
                        "start_time": "int",
                        "end_time": "int",
                        "picture_url": "str",
                        "description": "str",
                        "ticket_uri": "str",
                        "place": "str"
                    },
                ],
                "next": "/events?page=2&page_size=25&fbid=123",
                "prev": "/events?page=0&page_size=25&fbid=123"
              }
        """
        fbid = int(fbid)
        page = int(self.get_argument('page', '0'))
        limit = int(self.get_argument('page_size', '25'))

        logger.info("Getting events for just this user's friends...");
        events = [e for e in event.select_friends_events_for_user(fbid, offset=page*limit, limit=limit+1)]
        logger.info("Got {} events".format(len(events)))

        next, prev = self.get_next_and_prev(page, limit, events)

        self.write({
            'data': events[0:limit],
            'next': next,
            'prev': prev
        })

class UserInterestedEvents(BaseHandler):
    
    @tornado.gen.coroutine
    def get(self, fbid):
        """
        This endpoint requires the user to have marked some of their events as "interested"
            using PUT and setting the "interested" field to 1. It returns all the events the
            user has marked as interested.

        :param int fbid: The user's Facebook ID
        :param int page: Which page of results should be returned.
        :param int page_size: The number of results to return per-page.
        :returns: A list of events by the default ranking as well as standard pagination parameters.

          .. code-block:: JSON

              {
                "data": [
                    {
                        "id": "int",
                        "page_id": "int",
                        "page_name": "str",
                        "name": "str",
                        "attending_count": "int",
                        "interested_count": "int",
                        "noreply_count": "int",
                        "maybe_count": "int",
                        "start_time": "int",
                        "end_time": "int",
                        "picture_url": "str",
                        "description": "str",
                        "ticket_uri": "str",
                        "place": "str"
                    },
                ],
                "next": "/user/123/events?page=2&page_size=25",
                "prev": "/user/123/events?page=0&page_size=25"
              }
        """
        fbid = int(fbid)
        page = int(self.get_argument('page', '0'))
        limit = int(self.get_argument('page_size', '25'))

        logger.info("Getting events that this user is interested in...");
        events = [e for e in event.select_user_interested_events(fbid, offset=page*limit, limit=limit+1)]
        logger.info("Got {} events".format(len(events)))

        next, prev = self.get_next_and_prev(page, limit, events)

        self.write({
            'data': events[0:limit],
            'next': next,
            'prev': prev
        })
