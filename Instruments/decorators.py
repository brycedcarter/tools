"""
A set of useful decorators for use in the instruments library

Author: Bryce Carter
Date Created: 2021-06-18
"""

import signal


def _ignore_keyboard_interrupt(signal, frame):
    """
    This handler for keyboard interrupts (INT Signals) simply ignores the
    signal and displays a message indicating why
    """
    print('Please be patient while all items are gracefully closed...')


def SIGINT_protected(close_items, timeout):
    """
    This decorator should be used to protect a function (usually __main__)
    from being killed through SIGINT (Ctrl+C) multiple times before all items
    in "close_items" can be safely shut down.

    Normal protection mechanisms such as context manager for Instruments can
    still be used. This wrapper with trigger on a KeyboardInterrupt that is
    not handled at a lower level

    This decorator will call "close()" on each element in "close_items" and
    wait for them to be cleanly closed or for "timeout" to expire - whichever
    is comes first - before allowing keyboard interrupts to be processed again
    """
    def wrapper(func):
        def SIGINT_protected_func(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except KeyboardInterrupt:
                default_sigint_handler = signal.getsignal(signal.SIGINT)
                signal.signal(signal.SIGINT, _ignore_keyboard_interrupt)

                def timeout_error(*args):
                    raise TimeoutError('Timeout expired before all items'
                                       ' could be shut down')

                signal.signal(signal.SIGALRM, timeout_error)
                signal.alarm(timeout)

                for inst in list(close_items):
                    inst.close()

                signal.signal(signal.SIGINT, default_sigint_handler)
                signal.alarm(0)

        return SIGINT_protected_func
    return wrapper


def atomic_operation(func):
    """
    A decorator used to denote that a given method is complete operation that
    should be performed on the instrument without being interrupted
    Practically speaking, this means that it is functions decorated with this
    with acquire/require the operation_lock
    """
    def atomic_func(self, *args, **kwargs):
        with self._atomic_lock:
            return func(self, *args, *kwargs)
    return atomic_func


