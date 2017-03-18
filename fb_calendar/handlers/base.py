import urllib

import tornado.web


class BaseHandler(tornado.web.RequestHandler):

    def get_next_and_prev(self, page, size, results):
        """
        Given the parameters representing the current stage of pagination; this will create a link for the previous
            and next state.

        :param int page: The current page we're on
        :param int size: The number of results the user has requested for each page.
        :param results: The actual results. There is a tiny bit of logic around this since we request size + 1 to check
            whether or not to create a `next` link.
        :rtype: tuple(str, str)
        :returns: A tuple of the next and previous links. These will always be of type str.
        """
        next, prev = "", ""
        query = self.request.arguments
        query['page_size'] = [size]
        if len(results) > size:
            query['page'] = [page+1]
            next = "{}?{}".format(self.request.path, urllib.urlencode(query, True))
        if page > 0:
            query['page'] = [page-1]
            prev = "{}?{}".format(self.request.path, urllib.urlencode(query, True))

        return next, prev
