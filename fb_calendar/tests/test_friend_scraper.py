import json
import time

import mock
import tornado.testing
import tornado.gen

import app
import user
import friend_scraper 

class TestFriendScraper(tornado.testing.AsyncTestCase):

    @mock.patch('friend_scraper.time.sleep')
    @mock.patch('friend_scraper.User.select_all_new_active')
    @mock.patch('friend_scraper.facebook.get_friends_for_fbid')
    @mock.patch('friend_scraper.User.bulk_insert')
    @mock.patch('friend_scraper.Friendship.bulk_insert')
    @mock.patch('friend_scraper.User.update')
    @tornado.testing.gen_test
    def test_continuously_update_throttles(self, mock_user_update, mock_friendship_bulk_insert, mock_bulk_user_insert, mock_get_friends, mock_select_new, mock_sleep):
        now = int(time.time())
        mock_select_new.return_value = (u for u in [
            user.User(fbid=1, access_token='xxxx', expires_at=now, grants='user_friends', total_friends=0),
            user.User(fbid=2, access_token='xxxx', expires_at=now, grants='user_friends', total_friends=0),
            user.User(fbid=3, access_token='xxxx', expires_at=now, grants='user_friends', total_friends=0),
        ])

        @tornado.gen.coroutine
        def get_friends_coroutine(page_id, access_token):
            raise tornado.gen.Return([{'id': 4},{'id': 5},{'id': 6}]) 

        mock_get_friends.side_effect = get_friends_coroutine 

        friend_scraper.continuously_update()

        mock_get_friends.assert_any_call(1, 'xxxx')
        mock_get_friends.assert_any_call(2, 'xxxx')
        mock_get_friends.assert_any_call(3, 'xxxx')

        mock_sleep.assert_any_call(1)

        print mock_bulk_user_insert.mock_calls

        # This will be inserted three times. One for each new user above.
        mock_bulk_user_insert.assert_any_call([
            {
                'fbid': 4, 
                'access_token': None, 
                'expires_at': 0, 
                'grants': None, 
                'total_friends': 0
            }, 
            {
                'fbid': 5, 
                'access_token': None, 
                'expires_at': 0, 
                'grants': None, 
                'total_friends': 0
            }, 
            {
                'fbid': 6,
                'access_token': None, 
                'expires_at': 0, 
                'grants': None, 
                'total_friends': 0
            }
        ])

        mock_friendship_bulk_insert.assert_any_call([
            {'fbid': 1, 'friend_id': 4},
            {'fbid': 1, 'friend_id': 5},
            {'fbid': 1, 'friend_id': 6}
        ])
        mock_friendship_bulk_insert.assert_any_call([
            {'fbid': 2, 'friend_id': 4},
            {'fbid': 2, 'friend_id': 5},
            {'fbid': 2, 'friend_id': 6}
        ])
        mock_friendship_bulk_insert.assert_any_call([
            {'fbid': 3, 'friend_id': 4},
            {'fbid': 3, 'friend_id': 5},
            {'fbid': 3, 'friend_id': 6}
        ])
