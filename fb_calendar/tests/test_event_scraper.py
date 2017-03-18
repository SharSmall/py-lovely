import json

import mock
import tornado.testing
import tornado.gen

import app
import event_scraper

class TestPageScraper(tornado.testing.AsyncTestCase):

    def test_throttle(self):
        throttle = event_scraper.Throttle(rate=1)  # requests / sec
        for i in range(10):
            with throttle:
                pass

        assert throttle.wait_time > 0.9 and throttle.wait_time < 1.1, \
            "Throttle wait time was {} when we expected it to be about a second"


        throttle = event_scraper.Throttle(rate=10)  # requests / sec
        for i in range(10):
            with throttle:
                pass

        assert throttle.wait_time > 0.09 and throttle.wait_time < 0.11, \
            "Throttle wait time was {} when we expected it to be about 1/10 second"


    @mock.patch('event_scraper.throttle')
    @mock.patch('event_scraper.time.sleep')
    @mock.patch('page.get_all_pages')
    @mock.patch('event_scraper.facebook.get_events_by_page_id')
    @mock.patch('event_scraper.insert_events')
    @tornado.testing.gen_test
    def test_continuously_update_throttles(self, mock_insert_events, mock_get_events, mock_get_pages, mock_sleep, mock_throttle):
        mock_get_pages.return_value = [1, 2, 3]

        @tornado.gen.coroutine
        def get_events_coroutine(page_id):
            raise tornado.gen.Return('event ' + str(page_id))

        mock_get_events.side_effect = get_events_coroutine
        mock_throttle.wait_time = 0

        event_scraper.continuously_update()

        mock_get_events.assert_any_call(1)
        mock_get_events.assert_any_call(2)
        mock_get_events.assert_any_call(3)

        mock_sleep.assert_any_call(1)

        mock_insert_events.assert_any_call('event 1')
        mock_insert_events.assert_any_call('event 2')
        mock_insert_events.assert_any_call('event 3')

        assert mock_throttle.__enter__.called

    @mock.patch('event_scraper.page.get_new_pages')
    @mock.patch('event_scraper.facebook.get_events_by_page_id')
    @mock.patch('event_scraper.insert_events')
    @tornado.testing.gen_test
    def test_priority_update_does_not_throttle(self, mock_insert_events, mock_get_events, mock_get_pages):
        mock_get_pages.return_value = [4, 5, 6]

        @tornado.gen.coroutine
        def get_events_coroutine(page_id):
            raise tornado.gen.Return('event ' + str(page_id))

        mock_get_events.side_effect = get_events_coroutine

        event_scraper.priority_update()

        mock_insert_events.assert_any_call('event 4')
        mock_insert_events.assert_any_call('event 5')
        mock_insert_events.assert_any_call('event 6')
