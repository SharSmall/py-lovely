from __future__ import absolute_import

import logging
import json
import time

import tornado.web
import tornado.gen

from user import User as DBUser
from handlers.base import BaseHandler


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class User(BaseHandler):

    @tornado.gen.coroutine
    def post(self):
        """
        This endpoint creates a new user. If the user already exists the parameters passed will be used to update the
        existing user. The client is intended to implement the user facing facebook API to get the required
        variables. They all come as part of the authentication response.

        :param int fbid: The user's facebook id.
        :param str access_token: The access token to use to pull the user's data from FB.
        :param int expires_in: The length of time the access token is valid for in seconds.

        :returns: If we're successful in saving this user it'll return the current database record for them. This just
        means we'll rewrite the expires_in to reflect the unix timestamp at which the access token is no longer
        valid and we'll include the list of grants, comma delimited, that were approved by the user. NOTE: the
        expiry is approximate and can be seconds off.

          .. code-block:: JSON

              {
                  "user": {
                      "fbid": 12345,
                      "access_token": "xxxxxxxxxxxxxxx",
                      "expires_at": 123456789012,
                      "grants": "likes,events"
                  }
              }

        """
        logger.info("Got a user POST request")
        params = json.loads(self.request.body)
        user_id = int(params.get('fbid'))
        access_token = params.get('access_token')
        expires_in = params.get('expires_in')

        u = DBUser.select(pk=user_id)
        if not u:
            logger.info("Inserting user with access_token={}".format(access_token))
            DBUser.create(fbid=user_id,
                        access_token=access_token,
                        expires_at=time.time() + expires_in)
            u = DBUser.select(pk=user_id)
        else:
            logger.info("Updating user with access_token={}".format(access_token))
            u = DBUser.update(fbid=user_id,
                            access_token=access_token,
                            expires_at=time.time() + expires_in)

        self.write(json.dumps({
            'user': u
        }))

    def get(self):
        """
        Retrieves a previously stored user from the database. I can't think of a good reason to have this besides
        debugging and later when we add other attributes to the user and/or allow them to update a "profile".

        :param int fbid: The user's Facebook ID

        :returns: The user object.

          .. code-block:: JSON

              {
                  "user": {
                      "fbid": 12345,
                      "access_token": "xxxxxxxxxxxxxxx",
                      "expires_at": 123456789012,
                      "grants": "likes,events"
                  }
              }
        """
        fbid = self.get_argument('fbid')
        u = DBUser.select(pk=fbid)
        self.write({'user': u})
