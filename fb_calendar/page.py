import logging

from model import Model, ConnectionPool


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Page(Model):
    FIELDS = ['id', 'name', 'place_type', 'link',
              'most_recent_user_id', 'token_expires_at']
    PK = 'id'
    TABLE = 'page'


def get_all_pages():
    with ConnectionPool() as cursor:
        sql = "SELECT id FROM page;"
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        while row:
            yield row[0]
            row = cursor.fetchone()


def get_new_pages():
    with ConnectionPool() as cursor:
        sql = "SELECT id FROM page WHERE created_at = updated_at;"
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        while row:
            yield row[0]
            row = cursor.fetchone()
