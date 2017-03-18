import logging
import time
import dateutil.parser
import psycopg2

from model import Model, ConnectionPool


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Event(Model):
    FIELDS = ['id', 'page_id', 'page_name', 'name', 'attending_count', 'noreply_count',
              'interested_count', 'maybe_count', 'start_time',
              'end_time', 'picture_url', 'description', 'ticket_uri',
              'place']
    PK = 'id'
    TABLE = 'event'


class UserEvent(Model):
    FIELDS = ['event_id', 'fb_user_id']
    TABLE = 'user_event'


def select_upcoming_event_ids_for_page(page_id):
    logger.info("Selecting events for page....")
    with ConnectionPool() as cursor:
        sql = "SELECT event.id FROM event WHERE page_id = %s AND event.hidden = 0 AND event.start_time > EXTRACT(EPOCH FROM CURRENT_TIMESTAMP);"
        cursor.execute(sql, (page_id,))
        row = cursor.fetchone()
        while row:
            event_id = row[0]
            yield event_id
            row = cursor.fetchone()


def select_events_for_user(fbid, offset=0, limit=25):
    logger.info("Selecting events for user....")
    sql = "SELECT user_event.event_id, user_event.fb_user_id, event.name, " \
          "event.attending_count, event.interested_count, event.maybe_count, event.start_time " \
          "FROM user_event LEFT JOIN event ON user_event.event_id = event.id WHERE " \
          "user_event.fb_user_id = %s AND event.hidden = 0 AND " \
          "event.start_time > EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) AND attending_count > 20 ORDER BY " \
          "FLOOR(event.start_time/(60 * 60 * 24)) ASC, attending_count DESC OFFSET %s LIMIT %s;"

    with ConnectionPool() as cursor:
        cursor.execute(sql, (fbid, offset, limit))
        row = cursor.fetchone()
        while row:
            event_id = row[0]
            yield Event.select(pk=event_id)
            row = cursor.fetchone()

def select_user_interested_events(fbid, offset=0, limit=25):
    logger.info("Selecting events for user....")
    sql = "SELECT user_event.event_id, user_event.fb_user_id, event.name, " \
          "event.attending_count, event.interested_count, event.maybe_count, event.start_time " \
          "FROM user_event LEFT JOIN event ON user_event.event_id = event.id WHERE " \
          "user_event.fb_user_id = %s AND event.hidden = 0 AND " \
          "user_event.interested = 1 ORDER BY " \
          "FLOOR(event.start_time/(60 * 60 * 24)) ASC, attending_count DESC OFFSET %s LIMIT %s;"

    with ConnectionPool() as cursor:
        cursor.execute(sql, (fbid, offset, limit))
        row = cursor.fetchone()
        while row:
            event_id = row[0]
            yield Event.select(pk=event_id)
            row = cursor.fetchone()

def select_user_event(fbid, eventid):
    sql = "SELECT user_event.event_id, user_event.fb_user_id FROM user_event " \
          "WHERE user_event.event_id = %s AND user_event.fb_user_id = %s"

    with ConnectionPool() as cursor:
        cursor.execute(sql, (fbid, eventid))
        row = cursor.fetchone()
        if not row:
            return None
        return {event_id: row[0], user_id: row[1]}

def update_user_event(fbid, eventid):
    sql = "UPDATE user_event " \
          "SET event_id = %s AND fb_user_id = %s" \
          "WHERE event_id = %s AND fb_user_id = %s"

    with ConnectionPool() as cursor:
        cursor.execute(sql, (fbid, eventid, fbid, eventid))


def select_friends_events_for_user(fbid, offset=0, limit=25):
    logger.info("Selecting friend events for user....")
    sql = "SELECT event.id, COUNT(friendship.friend_id) AS likes FROM event LEFT JOIN user_event ON user_event.event_id = event.id LEFT JOIN " \
          "friendship ON friendship.friend_id = user_event.fb_user_id WHERE friendship.fbid = %s AND " \
          "event.start_time > EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) GROUP BY event.id ORDER BY likes DESC OFFSET %s LIMIT %s;"

    with ConnectionPool() as cursor:
        cursor.execute(sql, (fbid, offset, limit))
        row = cursor.fetchone()
        while row:
            event_id = row[0]
            yield Event.select(pk=event_id)
            row = cursor.fetchone()

def select_events_by_interested_count(offset=0, limit=25):
    sql = "SELECT event.id, event.name, " \
          "event.attending_count, event.interested_count, event.maybe_count, " \
          "event.start_time FROM event WHERE event.hidden = 0 AND "\
          "event.start_time > EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) AND attending_count > 20 ORDER BY " \
          "attending_count DESC OFFSET %s LIMIT %s;"

    with ConnectionPool() as cursor:
        cursor.execute(sql, (offset, limit))
        row = cursor.fetchone()
        while row:
            event_id = row[0]
            yield Event.select(pk=event_id)
            row = cursor.fetchone()

def select_events_by_attendance_ratio(offset=0, limit=25):
    sql = "SELECT event.id, event.name, " \
          "event.attending_count, event.interested_count, event.maybe_count, event.noreply_count, " \
          "event.start_time FROM event WHERE event.hidden = 0 AND " \
          "event.start_time > EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) AND noreply_count > 30 ORDER BY " \
          "attending_count / noreply_count DESC OFFSET %s LIMIT %s;"

    with ConnectionPool() as cursor:
        cursor.execute(sql, (offset, limit))
        row = cursor.fetchone()
        while row:
            event_id = row[0]
            yield Event.select(pk=event_id)
            row = cursor.fetchone()

def insert_events(events):
    for evt in events:
        if evt.get('start_time') is None:
            logger.warn("Start time didn't exist on an event. It definitely should have.")
            continue
        start_time = int(time.mktime(dateutil.parser.parse(evt.get('start_time')).timetuple()))
        end_time = int(time.mktime(dateutil.parser.parse(evt.get('end_time')).timetuple())) if evt.get('end_time') else None
        try:
            Event.create(id=evt['id'],
                           page_id=evt.get('page_id'),
                           page_name=evt.get('page_name'),
                           name=evt.get('name'),
                           attending_count=evt.get('attending_count'),
                           interested_count=evt.get('interested_count'),
                           noreply_count=evt.get('noreply_count'),
                           maybe_count=evt.get('maybe_count'),
                           start_time=start_time,
                           end_time=end_time,
                           picture_url=evt.get('picture', {}).get('data', {}).get('url', ''),
                           description=evt.get('description'),
                           ticket_uri=evt.get('ticket_uri'),
                           place=evt.get('place'))
        except psycopg2.IntegrityError, e:
            pass # Optimistic insert
