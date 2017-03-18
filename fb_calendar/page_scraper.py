import time
import logging

import tornado.gen
import tornado.ioloop
import psycopg2

from services import facebook


import event

from user import User 
from page import Page
from event import UserEvent
from lib.throttle import Throttle


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
throttle = Throttle()


@tornado.gen.coroutine
def continuously_update():
    """
    Pulls all the user's likes from the FB api and throw 'em in the database.
    This guy loops every one second, grabbing all the users that just 
    signed up.

    This method has no return value, just the side effect that now the database will be full of that user's pages
    and the associated events.

    We don't need to drill down into the user's friends since they were at one point also all new active users.

    :param int user_id: The user's fbid for which to pull likes.
    """
    logger.info("Running continuously_update()")
    users = User.select_all_new_active()
    for u in users:
        logger.info("Fetching pages for user {}".format(u.fbid))
        pages = yield facebook.get_liked_pages(u.fbid, u.access_token)
        for pg in pages:
            logger.info("Creating page {}".format(pg.get('id')))
            try:
                Page.create(id=pg.get('id'),
                             name=pg.get('name'),
                             place_type=pg.get('place_type'),
                             link=pg.get('link'),
                             most_recent_user_id=u.fbid,
                             token_expires_at=u.expires_at)
            except psycopg2.IntegrityError, e:
                pass # Optimistic INSERT

            event_ids = event.select_upcoming_event_ids_for_page(pg.get('id'))
            for event_id in event_ids:
                try:
                    UserEvent.create(fb_user_id=u.fbid, event_id=event_id)
                except psycopg2.IntegrityError, e:
                    pass # Optimistic INSERT

    with throttle:
        logger.info("Calling again in a second.")
        tornado.ioloop.IOLoop.current().call_later(1, continuously_update)


if __name__ == '__main__':
    logger.info("Creating ioloop.")
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(continuously_update)
    ioloop.start()
