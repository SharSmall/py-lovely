import logging

import model 


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class User(model.Model):
    FIELDS = ['fbid', 'access_token', 'expires_at', 'grants', 'total_friends']
    TABLE = 'fb_user'
    PK = 'fbid'


    @classmethod
    def select_all_new_active(kls): 
        """
        Selects all users who have just signed up/logged in for the first time. The condtions we
            check to ensure the user has _just_ logged on for the first time are: 
            
            1. total_friends are set to 0 (which we change after a successful pull) and 
            2. expires_at > 0 since new users are distinguished from _pulled_ users by the fact
                that they have an access_token.

        NOTE: While this method is running it consumes one database connection.
        """
        with model.ConnectionPool() as cursor:
            sql = "SELECT {} FROM {} WHERE created_at = updated_at AND expires_at > 0;".format(
              ",".join(kls.FIELDS), kls.TABLE)
            cursor.execute(sql)
            row = cursor.fetchone()
            while row:
                yield User(**{field: row[col] for col, field in enumerate(kls.FIELDS)})
                row = cursor.fetchone()
    
    @classmethod
    def select_all_new(kls):
        """
        Selects all new users. This includes active AND passive (friends of 
            active users).

        """
        with model.ConnectionPool() as cursor:
            sql = "SELECT {} FROM {} WHERE created_at = updated_at;".format(
                ",".join(kls.FIELDS), kls.TABLE)
            cursor.execute(sql)
            row = cursor.fetchone()
            while row:
                yield User(**{field: row[col] for col, field in enumerate(kls.FIELDS)})
                row = cursor.fetchone()

