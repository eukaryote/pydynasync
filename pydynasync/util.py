"""
Miscellaneous utilities.
"""
import inspect
import sys
import traceback
import weakref

_weakkeydict_codes = tuple(
    func.__code__ for _, func in
        inspect.getmembers(weakref.WeakKeyDictionary, inspect.isfunction)
)

def is_weakref_call(*, framenum=2):
    """
    Answer whether being called by a weakref method that we use.

    This walks the stack starting at the `framenum` frame (0 is current frame),
    which defaults to 2 for the common case of code in this library
    calling this method.
    """
    for frame, _ in traceback.walk_stack(sys._getframe(framenum)):
        try:
            if frame.f_code in _weakkeydict_codes:
                return True
        except AttributeError:
            pass
    return False
