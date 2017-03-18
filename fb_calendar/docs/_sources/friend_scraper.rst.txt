Friend Scraper
--------------

This module looks for all new active users. Then it queries for their friends that have the app enabled and saves them as passive users (if they don't exist as active users for whatever reason e.g. signup failed).

Next the process indicates a connection between the user and their friends by creating a record in the friendship table.

.. automodule:: friend_scraper 
   :members:
