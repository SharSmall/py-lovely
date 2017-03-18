import time
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Throttle(object):
    """
    Provides a throttling mechanism for things that need to be rate limited. If this wasn't
        intended to run in an ioloop we would simply block in __enter__ by sleeping wait_time
        seconds. Since we're in an async process sleeping would cause the process to block which
        would delay execution of the priority queue (which is very bad).

    Instead of sleeping, then, we just indicate how much time should be waited before this method
        is called and we trust the ioloop to do it's job.
    """

    def __init__(self, rate=0.00333):
        self.rate = rate  # Calls per second (default is once every 5 minutes)
        self.__reset_counter()

    def __enter__(self):
        """
        Each time we enter this context manager it checks the number of calls since the last time it
            was called (always 1) against the rate limit with the elapsed time from the last call in
            mind.

        It then sets the `wait_time` attribute and resets the call and elapsed_time counter (which,
            for a daemon process is necessary to avoid overflows). It's python so probably overflows
            are not a problem, but I can't think of a good reason not to do this.
        """
        self.calls += 1.
        elapsed_s = time.time() - self.last_called
        self.wait_time = 0.
        if self.calls / elapsed_s > self.rate:
            self.wait_time = self.calls / self.rate
            logger.warning("Throttle: Waiting {} seconds".format(self.wait_time))
        self.__reset_counter()
        return self

    def __exit__(self, *args, **kwargs):
        pass  # la la la, lee lee lee

    def __reset_counter(self):
        self.calls = 0
        self.last_called = time.time()
