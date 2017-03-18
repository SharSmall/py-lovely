import os.path
import logging

import tornado.ioloop
import tornado.template
import tornado.web

import settings

import handlers.event
import handlers.user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        template_path = settings.get('app_root') + '/templates'
        if not os.path.exists(template_path):
            self.write('{} DNE'.format(template_path))
            return
        loader = tornado.template.Loader(template_path)
        self.write(loader.load(template_path + '/index.html').generate(fb_app_id=settings.get('fb_app_id')))


def make_app():
    logger.info("Starting app...")
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/user/(?P<s_user_id>[0-9]+)/event/(?P<s_event_id>[0-9]+)", handlers.event.UserEvents),
        (r"/user", handlers.user.User),
        (r"/user/([0-9]+)/events/friends", handlers.event.FriendEvents),
        (r"/events", handlers.event.UserEvents),
        (r"/feed/events/big", handlers.event.BigEvents),
        (r"/feed/events/cool", handlers.event.CoolEvents)
    ])

if __name__ == "__main__":
    logger.info("started main routine")
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
