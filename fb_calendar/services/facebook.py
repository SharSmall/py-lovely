import logging
import time
import json

import tornado.httpclient
import tornado.gen

from page import Page
from user import User


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


API_BASE = 'https://graph.facebook.com'
LIKE_ENDPOINT = '/%s/likes?fields=is_community_page,place_type,name,link,picture&access_token=%s'
EVENT_ENDPOINT = '/%s/events?fields=picture,name,attending_count,interested_count,noreply_count,maybe_count,start_time,end_time,picture_url,description,ticket_uri,place&access_token=%s&since=%s'
FRIENDS_ENDPOINT = '/%s/friends?access_token=%s'


@tornado.gen.coroutine
def get_friends_for_fbid(user_id, access_token):
    """
    Given a Facebook user_id and access_token; this method pulls the 
        associated user's friends. It stores them all before returning. If
        the user has shitloads of friends that means it can take some time.

    Facebook is nice enough to bound this at 5K, but that's not guaranteed to
        be the same for all time. We should just consider that large but not
        unbounded.

    :param int user_id: The user's Facebook ID
    :param int access_token: The access token with the user_friends grant 
        approved.

    :returns: A list of user specs. That's a dictionary where the keys are 
        the fields of user.User.FIELDS (the fields on the user model) and 
        the values are either None or the correct type for the database 
        column.
    """
    all_friends = []
    async_client = tornado.httpclient.AsyncHTTPClient()
    nxt = API_BASE + FRIENDS_ENDPOINT % (user_id, access_token) 
    while nxt:
        logger.info("Fetching page url {}".format(nxt))
        friends = json.loads((yield async_client.fetch(nxt)).body)
        logger.info("Found {} friends in this batch".format(
            len(friends.get('data', []))))
        all_friends += friends.get('data')
        nxt = friends.get('paging').get('next')

    logger.info("Found total {} friends".format(len(all_friends)))

    raise tornado.gen.Return(all_friends)


@tornado.gen.coroutine
def get_liked_pages(user_id, access_token):
    async_client = tornado.httpclient.AsyncHTTPClient()
    nxt = API_BASE + LIKE_ENDPOINT % (user_id, access_token)
    all_liked_pages = []
    while nxt:
        logger.info("Fetching page url {}".format(nxt))
        liked_pages = json.loads( (yield async_client.fetch(nxt)).body )
        logger.info(json.dumps(liked_pages, indent=2))
        logger.info("Found {} in this batch".format(len(liked_pages.get('data', []))))
        all_liked_pages += liked_pages.get('data', [])
        nxt = liked_pages['paging'].get('next')

    logger.info("Found {} total liked pages".format(all_liked_pages))

    raise tornado.gen.Return(all_liked_pages)


@tornado.gen.coroutine
def get_events_by_page_id(page_id, page_name=None, access_token=None):
    """
    :param int page_id: The Facebook ID of the user
    :returns: A list of events from the page.
    """
    logger.info("Called get_events_by_page_id")
    async_client = tornado.httpclient.AsyncHTTPClient()
    all_events = []

    if not access_token or not page_name:
        pg = Page.select(pk=page_id)
        page_name = pg.get('name')
        user_id = pg.get('most_recent_user_id')
        logger.info("Most recent user for this page is #{}".format(user_id))
        u = User.select(pk=user_id)
        access_token = u.get('access_token')
        expires_at = u.get('expires_at')
        if expires_at < time.time():
            raise tornado.gen.Return([])

    nxt = API_BASE + EVENT_ENDPOINT % (page_id, access_token, int(time.time()))
    while nxt:
        logger.info("Fetching page url {}".format(nxt))
        events = json.loads((yield async_client.fetch(nxt)).body)
        logger.info("Found {} events in this batch".format(len(events.get('data', []))))
        all_events += events.get('data', [])
        nxt = events.get('paging', {}).get('next')

    logger.info("Found {} total evevnts".format(len(all_events)))
    for evt in all_events:
        evt['page_id'] = page_id
        evt['page_name'] = page_name
        evt['place'] = evt.get('place', {}).get('name', None)

    raise tornado.gen.Return(all_events)


@tornado.gen.coroutine
def get_events_by_user_id(user_id):
    u = User.select(pk=user_id)
    access_token = u.get('access_token')
    liked_pages = yield get_liked_pages(user_id, access_token)
    page_events = []
    for liked_page in liked_pages:
        page_events += yield get_events_by_page_id(liked_page.get('id'), liked_page.get('name'), access_token)
    raise tornado.gen.Return(page_events)
