"""A small on-disk cache for things that are slow to build (the catalogue, mainly).

Files live in CACHE_DIR, which the app creates with mode 0700; only the app process writes there.
"""
import os
import pickle
import tempfile
import time

from flask import current_app


def _path(key):
    return os.path.join(current_app.config["CACHE_DIR"], f"{key}.pickle")


def get(key, max_age):
    path = _path(key)
    try:
        if time.time() - os.path.getmtime(path) > max_age:
            return None
        with open(path, "rb") as f:
            return pickle.load(f)
    except (OSError, EOFError, pickle.UnpicklingError):
        return None


def put(key, value):
    fd, tmp = tempfile.mkstemp(dir=current_app.config["CACHE_DIR"])
    with os.fdopen(fd, "wb") as f:
        pickle.dump(value, f)
    os.replace(tmp, _path(key))


def clear(key):
    try:
        os.remove(_path(key))
    except FileNotFoundError:
        pass
