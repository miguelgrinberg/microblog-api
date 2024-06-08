# This module implements safe replacements for the deprecated datetime.utcnow()
# function of the Python standard library.
# For details see this blog post:
# https://blog.miguelgrinberg.com/post/it-s-time-for-a-change-datetime-utcnow-is-now-deprecated

from datetime import datetime, timezone


def aware_utcnow():
    return datetime.now(timezone.utc)


def naive_utcnow():
    return aware_utcnow().replace(tzinfo=None)
