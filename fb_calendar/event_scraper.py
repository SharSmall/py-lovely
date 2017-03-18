import time
import logging

import tornado.gen
import tornado.ioloop

from services import facebook
import page

from event import insert_events
from lib.throttle import Throttle


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

throttle = Throttle()


@tornado.gen.coroutine
def priority_update():
    """
    This method pulls the pages users _just_ added to the database by either
      1) logging in for the first time or
      2) logging in again after liking new pages (or pages we didn't pull last time they logged in
         due to errors or whatever).
      3) Having a friend log in for the first time (and hence they were pulled by the 
         friend_scraper process).

    We first query for all _new_ pages. These are all pages for which created_at == updated_at. Then
    we just loop through all those pages, querying Facebook for their latest; and saving that
    to the DB.
    """
    new_pages = page.get_new_pages()
    for page_id in new_pages:
        events = yield facebook.get_events_by_page_id(page_id)
        insert_events(events)

    # This is to avoid hitting the DB too hard when there are no updates to make.
    tornado.ioloop.IOLoop.current().call_later(1, priority_update)


@tornado.gen.coroutine
def continuously_update():
    """
    This method lets us avoid pulling the complete history of pages all the damn time. It solves a
    number of problems. First, when a new user has liked a page an older user has already caused
    to be saved in our database; we don't have to pull anything for that page. This means faster
    API response times at a user's initial login. The second problem this solves is; when that same
    thing occurs (we're pulling a page already saved) we don't have to pull the whole history for
    the page.

    Every rate_limit (5 minutes) seconds we pull _all_ the pages in our database (USING A CURSOR,
    NOT RAM). Then we go through all those pages requesting events. We request events for which
    the starting time is in the future, obviously, because past events are no longer relevant.

    """
    to_update = page.get_all_pages()
    for page_id in to_update:
        logger.info("Updating {}".format(page_id))
        events = yield facebook.get_events_by_page_id(page_id)
        insert_events(events)
        time.sleep(1) # Rate limit at a granular level, too.

    with throttle:
        tornado.ioloop.IOLoop.current().call_later(throttle.wait_time, continuously_update)


if __name__ == '__main__':
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(continuously_update)
    ioloop.add_callback(priority_update)
    ioloop.start()
