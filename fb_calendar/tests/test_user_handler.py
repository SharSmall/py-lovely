import datetime
import json
import mock
import uuid
import time

import tornado.httpclient
import tornado.gen
import tornado.testing


import app
import handlers.user as handlers

class TestUserHandler(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return app.make_app()

    @mock.patch('handlers.user.DBUser')
    def test_user_post_update_case(self, mock_DBUser):
        expires_at = int(time.time())
        access_token = str(uuid.uuid4())
        mock_user = {
            'fbid': 456,
            'access_token': access_token,
            'grants': 'email,user_likes',
            'expires_at': expires_at,
        }
        mock_DBUser.select.return_value = mock_user
        mock_DBUser.update.return_value = mock_user

        @tornado.gen.coroutine
        def pull_coroutine(fbid):
            pass

        with mock.patch('handlers.user.User.write') as mock_write:
            with mock.patch('time.time') as mock_time:
                mock_time.return_value = 0
                resp = self.fetch('/user', method='POST', body=json.dumps({
                    'fbid': 456,
                    'access_token': access_token,
                    'expires_in': 120
                }))

            assert mock_write.mock_calls, "write() not called"
            mock_write.assert_any_call(json.dumps({'user': mock_user}))

        mock_DBUser.update.assert_any_call(fbid=456,
                                           access_token=access_token,
                                           expires_at=120)


    @mock.patch('handlers.user.DBUser')
    def test_user_post_create_case(self, mock_DBUser):
        expires_at = int(time.time())
        access_token = str(uuid.uuid4())
        mock_user = {
            'fbid': 456,
            'access_token': access_token,
            'expires_at': expires_at,
            'grants': 'email,user_likes'
        }
        mock_DBUser.select.return_value = None

        @tornado.gen.coroutine
        def pull_coroutine(fbid):
            yield None

        with mock.patch('time.time') as mock_time:
            mock_time.return_value = 0
            resp = self.fetch('/user', method='POST', body=json.dumps({
                'fbid': 456,
                'access_token': access_token,
                'expires_in': 120
            }))

        mock_DBUser.create.assert_any_call(fbid=456,
                                           access_token=access_token,
                                           expires_at=120)

    @mock.patch('handlers.user.DBUser')
    def test_user_handler_get(self, mock_DBUser):
        expires_at = int(time.time())
        access_token = str(uuid.uuid4())
        mock_user = {
            'fbid': 456,
            'access_token': access_token,
            'expires_at': expires_at,
            'grants': 'email,user_likes'
        }
        mock_DBUser.select.return_value = mock_user

        resp = self.fetch('/user?fbid=456')

        target = json.loads(resp.body)
        print target

        assert target.get('user') == mock_user

    @mock.patch('event.update_user_event')
    @mock.patch('event.select_user_event')
    @mock.patch('handlers.event.UserEvent')
    def test_user_post_save_event_exists(self, mock_user_event, mock_select_user_event, mock_update_user_event):
        mock_select_user_event.return_value = {'event_id': 3, 'user_id': 456}

        resp = self.fetch('/user/456/event/3', method='POST', body=json.dumps({}))

        target = json.loads(resp.body)

        assert target.get('user_id') == 456
        assert target.get('event_id') == 3
        mock_update_user_event.assert_called_once_with(456, 3)

    @mock.patch('event.update_user_event')
    @mock.patch('event.select_user_event')
    @mock.patch('handlers.event.UserEvent')
    def test_user_post_save_event_new(self, mock_UserEvent, mock_select_user_event, mock_update_user_event):
        mock_select_user_event.return_value = None

        resp = self.fetch('/user/456/event/3', method='POST', body=json.dumps({}))

        target = json.loads(resp.body)

        assert target.get('user_id') == 456
        assert target.get('event_id') == 3
        mock_UserEvent.create.assert_called_once_with(event_id=3,fb_user_id=456) 
