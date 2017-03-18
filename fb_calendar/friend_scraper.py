import time
import logging

import tornado.gen
import tornado.ioloop

from services import facebook
import page
from user import User 
from friendship import Friendship


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@tornado.gen.coroutine
def continuously_update():
    """
    Now we're getting into territory that really warrants a message bus. This 
    method looks for users whose friend count is 0. The first thing we need 
    to do here is set that friend count to -1 optimistically. This allows this
    process to run in parallel with other instances (which is probably 
    necessary since it's pretty heavy).

    We select those users whose friend coutn is 0 with a database query every so 
    often. That results in a lot of unnecessary querying! How this _should_ 
    work is simple: 
        
        1. User signs up or logs into the client. 
        2. The backend returns a user object with a friend count of 0
        3. The client sends a message along the bus to an event driven 
           queuereader waiting to process the friend list for the target user.

    You're probably asking "why don't we just have the client POST to a new 
    endpoint?" This process is long-winded. Users can have up to 5K friends, 
    which means a POST endpoint could take > 10s to return normally. Let's
    just avoid gateway timeouts and the like on edge cases by daemonizing
    this.  

    Ultimately we should be implementing NSQd (preferred) or Kafka (second). When
    that happens we'll convert this to a queuereader. This is good enough for
    now.
    """
    new_users = User.select_all_new_active() 
    for user in new_users:
        try:
            logger.info("Updating {}".format(user.fbid))
            fb_users = yield facebook.get_friends_for_fbid(user.fbid, user.access_token)
            user_specs = []
            friendship_specs = []
            for fb_user in fb_users:
                user_specs.append({
                    'fbid': fb_user.get('id'),
                    'access_token': None,
                    'expires_at': 0, # Indicates not to pull friends for this user.
                    'grants': None,
                    'total_friends': 0
                })
                friendship_specs.append({
                    'fbid': user.fbid,
                    'friend_id': fb_user.get('id') 
                })
              
            # These inserts SHOULD ignore errors and error on duplicate entries. 
            User.bulk_insert(user_specs)	
            Friendship.bulk_insert(friendship_specs)

            # This update indicates the whole process was successful.
            User.update(fbid=user.fbid, total_friends=len(friendship_specs)) 
             
            time.sleep(1) # Rate limit at a granular level, too.
        except Exception, e:
            logger.exception(e) #  Log the error but continue. We never gonna die!

    tornado.ioloop.IOLoop.current().call_later(5, continuously_update)


if __name__ == '__main__':
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(continuously_update)
    ioloop.start()
