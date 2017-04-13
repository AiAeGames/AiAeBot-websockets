import threading
from collections import defaultdict

class Locker(object):
    def __init__(self, delay=None, user=""):
        self.delay = delay if delay or delay == 0 and type(delay) == int else 5
        self.locked = False

    def lock(self):
        if not self.locked:
            if self.delay > 0:
                self.locked = True
                t = threading.Timer(self.delay, self.unlock, ())
                t.daemon = True
                t.start()
        return self.locked

    def unlock(self):
        self.locked = False
        return self.locked


def cooldown(delay):
    def decorator(func):
        if not hasattr(func, "__cooldowns"):
            func.__cooldowns = defaultdict(lambda: Locker(delay))

        def inner(*args, **kwargs):
            nick = args[2].source.nick
            user_cd = func.__cooldowns[nick]
            if user_cd.locked:
                return

            ret = func(*args, **kwargs)
            user_cd.lock()
            return ret
        return inner
    return decorator