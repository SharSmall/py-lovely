import logging
import collections

import psycopg2

import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ConnectionPool(object):
    _pool = collections.deque()
    _initialized = False

    def __init__(self):
        self.__dispatched = collections.deque()
        self.__cursors = collections.deque()

        if not ConnectionPool._initialized:
            ConnectionPool._initialized = True
            for i in xrange(5):
                self.__establish_connection()


    def __establish_connection(self):
        conn = psycopg2.connect(database=settings.get('dbname'),
                                user=settings.get('dbuser'),
                                password=settings.get('dbpassword'))
        ConnectionPool._pool.append(conn)
        logger.warning("Establishing new connection: #{}".format(len(ConnectionPool._pool)))


    def __enter__(self):
        if not ConnectionPool._pool:
            self.__establish_connection()

        conn = ConnectionPool._pool.popleft()
        cursor = conn.cursor()
        self.__dispatched.append(conn)
        self.__cursors.append(cursor)
        return cursor


    def __exit__(self, exc_type, exc_val, tb):
        while self.__dispatched:
            conn = self.__dispatched.popleft()
            ConnectionPool._pool.append(conn)

            if exc_type is psycopg2.IntegrityError:
                conn.rollback()
            elif not conn.closed:
                conn.commit()

        while self.__cursors:
            cursor = self.__cursors.popleft()
            if not cursor.closed:
                cursor.close()


class Model(object):

    def __init__(self, *args, **kwargs):
        for field, value in kwargs.items():
            if field not in self.FIELDS:
                raise NameError("{} is not a valid argument".format(field)) 
            setattr(self, field, value)


    @classmethod
    def select(kls, pk=None):
        sql = "SELECT {} FROM {} WHERE {} = %s;".format(
            ",".join(kls.FIELDS), kls.TABLE, kls.PK
        )
        with ConnectionPool() as cursor:
            cursor.execute(sql, (pk,))
            row = cursor.fetchone()
            if not row:
                return None
            return {field: row[col]
                    for col, field in enumerate(kls.FIELDS)}


    @classmethod
    def create(kls, **kwargs):
        fields_passed = [field for field in kls.FIELDS if field in kwargs]
        sql = "INSERT INTO {} ({}) VALUES ({});".format(
            kls.TABLE, ",".join(fields_passed), ",".join(["%s"] * len(kwargs))
        )
        with ConnectionPool() as cursor:
            cursor.execute(sql, tuple([
                kwargs[field]
                for field in fields_passed]))

        return kwargs


    @classmethod
    def update(kls, **kwargs):
        pk = kwargs.pop(kls.PK)
        fields_passed = [field for field in kls.FIELDS if field in kwargs]
        keyvals = ",".join(["{} = %s".format(f) for f in fields_passed])
        sql = "UPDATE {} SET {} WHERE {} = %s;".format(
            kls.TABLE, keyvals, kls.PK
        )

        logger.info("SQL: {}, fields: {}".format(sql, tuple([kwargs[field]
                                   for field in fields_passed] + [pk])))
        with ConnectionPool() as cursor:
            cursor.execute(sql, tuple([kwargs[field]
                                       for field in fields_passed] + [pk]))

        return kwargs
    
   
    @classmethod
    def bulk_insert(kls, models):
        """
        Inserts models in bulk. You can pass as many as you like but we'll only send 50 at a time. 
            I'm not sure if postgres has the maximum packet size issue mysql does. If it does this
            will get around it. If not... well it's just good practice to batch large calls.

        TODO: Ignore errors on the bulk insert to avoid having to check if users were previously 
            inserted.

        :param list(dict) models: A list of model specs. These are just dictionaries with the values
            of cls.FIELDS as the keys. The values need to either be None or valid types that 
            correspond to the types set in the database.

        :returns: Nada.
        """
        values = []
        for model in models:
            values.append(tuple([model.get(field) for field in kls.FIELDS]))

        for idx in range(0, len(values), 50):
            batch = values[idx:idx+50]
            sql = "INSERT INTO {} ({}) VALUES {};".format(
                kls.TABLE, ",".join(kls.FIELDS), 
                ','.join(['(' + ",".join(['%s']*len(kls.FIELDS)) + ')']*len(batch)))

            with ConnectionPool() as cursor:
                cursor.execute(sql, [_ for __ in batch for _ in __])


    @classmethod
    def count(kls):
        with ConnectionPool() as cursor:
            cursor.execute("SELECT COUNT(*) FROM {};".format(self.TABLE))
            return cursor.fetchone()[0]
