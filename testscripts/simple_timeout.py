#! /usr/bin/env python

import signal


class TimeoutException(Exception):
    pass


def get_name():
    def timeout_handler(signum, frame):
        raise TimeoutException()

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(3)  # triggers alarm in 3 seconds

    try:
        # print "please enter a name: "
        # name = sys.stdin.readline()
        name = raw_input('please enter a name: ')
    except TimeoutException:
        return "default value"
    return name

if __name__ == '__main__':
    name = get_name()
    print "got: %s" % name

# -fin-
