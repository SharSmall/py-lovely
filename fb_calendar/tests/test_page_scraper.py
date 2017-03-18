import datetime
import uuid
import time

import tornado
import mock
import tornado.testing

import page_scraper
from user import User


class TestPageScraper(tornado.testing.AsyncTestCase):

    @mock.patch('page_scraper.User')
    @mock.patch('page_scraper.facebook.get_liked_pages')
    @mock.patch('page_scraper.Page')
    @mock.patch('page_scraper.event.select_upcoming_event_ids_for_page')
    @mock.patch('page_scraper.UserEvent')
    @tornado.testing.gen_test
    def test_update_continuously(self, mock_UserEvent, mock_select_upcoming, mock_Page, mock_get_liked_pages, mock_DBUser):
        # This mock represents a tornado.httpclient.HTTPRequest
        mock_request = mock.MagicMock()

        now = datetime.datetime.now()
        expires_at = int(time.time())
        mock_user = {
            'fbid': 123,
            'access_token': str(uuid.uuid4()),
            'expires_at': expires_at,
            'grants': 'email,user_likes'
        }

        @tornado.gen.coroutine
        def mock_pages_coroutine(user_id, access_token):
            return [{
                'id': 12,
                'name': 'Page One',
                'place_type': 'Place Type One',
                'link': 'http://example.com/1',
                'created_at': now,
                'updated_at': now,
                'most_recent_user_id': 123,
                'token_expires_at': expires_at
            },{
                'id': 22,
                'name': 'Page Two',
                'place_type': 'Place Type Two',
                'link': 'http://example.com/2',
                'created_at': now,
                'updated_at': now,
                'most_recent_user_id': 123,
                'token_expires_at': expires_at
            },{
                'id': 32,
                'name': 'Page Three',
                'place_type': 'Place Type Three',
                'link': 'http://example.com/3',
                'created_at': now,
                'updated_at': now,
                'most_recent_user_id': 123,
                'token_expires_at': expires_at
            }]
        mock_select_upcoming.return_value = [1, 2, 3, 4, 5]
        mock_DBUser.select_all_new_active.return_value = [User(**mock_user)]
        mock_get_liked_pages.side_effect = mock_pages_coroutine

        # This lets us call the private method independent of surrounding logic and architecture
        # it may be dependent on. Hence it is a UNIT test.
        target = yield page_scraper.continuously_update()
        assert target is None, "We didn't expect the handler to return anything!"
        mock_get_liked_pages.assert_any_call(123, mock_user.get('access_token'))
        pages = yield mock_pages_coroutine(None, None)
        for page in pages:
            mock_Page.create.assert_any_call(id=page.get('id'),
                name=page.get('name'),
                place_type=page.get('place_type'),
                link=page.get('link'),
                most_recent_user_id=mock_user.get('fbid'),
                token_expires_at=expires_at)

        mock_select_upcoming.assert_any_call(12)
        mock_select_upcoming.assert_any_call(22)
        mock_select_upcoming.assert_any_call(32)
        mock_UserEvent.create.assert_any_call(fb_user_id=123, event_id=1)
        mock_UserEvent.create.assert_any_call(fb_user_id=123, event_id=2)
        mock_UserEvent.create.assert_any_call(fb_user_id=123, event_id=3)
        mock_UserEvent.create.assert_any_call(fb_user_id=123, event_id=4)
        mock_UserEvent.create.assert_any_call(fb_user_id=123, event_id=5)
