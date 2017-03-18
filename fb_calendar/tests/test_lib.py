import unittest

from lib.throttle import Throttle

class TestLib(unittest.TestCase):

    def test_throttle(self):
        throttle = Throttle(rate=1)  # requests / sec
        for i in range(10):
            with throttle:
                pass

        assert throttle.wait_time > 0.9 and throttle.wait_time < 1.1, \
            "Throttle wait time was {} when we expected it to be about a second"


        throttle = Throttle(rate=10)  # requests / sec
        for i in range(10):
            with throttle:
                pass

        assert throttle.wait_time > 0.09 and throttle.wait_time < 0.11, \
            "Throttle wait time was {} when we expected it to be about 1/10 second"
