import os
import json
import logging


logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


_settings = {}


class MISSING:
    pass


def get(name):
    setting = _settings.get(name, MISSING)
    if setting is MISSING:
        setting = os.environ.get(name, MISSING)
    if setting is MISSING:
        raise RuntimeError("Desired setting, {}, does not exist in secret settings or environment".format(name))
    return setting

try:
    with open('/fb_calendar/local/app/secrets.json', 'rb') as secrets:
        _settings.update(json.loads(secrets.read()))
except Exception, e:
    logger.exception(e) # Just log. We need to catch here so CI tests pass

