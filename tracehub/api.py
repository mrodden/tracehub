import base64
import os
import json


TRACE_DIR = os.path.abspath("traces")


def create_key():
    key = None

    while not key:
        # 64 bit random
        r = os.urandom(8)
        k = base64.urlsafe_b64encode(r).decode("utf8").strip("=")

        # check for collision
        if not get_trace(k):
            key = k

    return key


def trace_path(key):
    return os.path.join(TRACE_DIR, key)


def create_trace(key, **kwargs):
    path = trace_path(key)
    with open(path, "w") as mdf:
        json.dump(kwargs, mdf)

    return kwargs


def get_traces():
    traces = []
    for f in os.listdir(TRACE_DIR):
        if not f.endswith(".trace"):
            t = get_trace(f)
            t["key"] = f
            if t:
                traces.append(t)

    traces = sorted(traces, key=lambda x: x["upload_time"], reverse=True)

    return traces[:50]


def get_trace(key):
    path = trace_path(key)

    if not os.path.exists(path):
        return None

    with open(path) as mdf:
        trace_md = json.load(mdf)

    return trace_md


def get_trace_content_path(key):
    return TRACE_DIR, ".".join([key, "trace"])
