from datetime import datetime, timedelta


class TimeoutCalculator:
    """Keeps track of how much time is left"""
    def __init__(self, timeout_seconds):
        self._end_time = datetime.now() + timedelta(seconds=timeout_seconds)

    def time_left_now(self):
        now = datetime.now()
        if now > self._end_time:
            return 0
        else:
            return (self._end_time - now).total_seconds()
