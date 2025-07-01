import os
import datetime
import time

import flask
from flask import Flask, render_template, request

from tracehub import api


app = Flask(__name__)


hostname = os.environ.get("TRACEHUB_HOSTNAME")
if hostname:
    server_name = "%s:%d" % (hostname, 5000)
    app.config["SERVER_NAME"] = server_name


app.config["PREFERRED_URL_SCHEME"] = "http"
app.config["APPLICATION_ROOT"] = "/"


@app.route("/")
def index():
    traces = api.get_traces()
    return render_template("index.html.j2", traces=traces)


@app.route("/tracehub.sh")
def tracehub_cli():
    return render_template("tracehub.sh.j2"), 200, {"Content-Type": "text/plain"}


@app.route("/u/<username>")
def user_list(username):
    if not username.isalnum():
        flask.abort(404)

    try:
        entries = os.listdir("data/%s" % username)
    except FileNotFoundError:
        flask.abort(404)

    return render_template("userlist.html.j2", trace_entries=entries, username=username)


@app.route("/api/post_trace", methods=["POST"])
def post_trace():
    if "trace" not in request.files:
        flask.abort(400)

    file = request.files["trace"]
    trace_name = request.form.get("name")
    username = request.form.get("user")

    new_key = api.create_key()
    ts = time.time()
    directory, name = api.get_trace_content_path(new_key)
    file.save(os.path.join(directory, name))
    stats = os.stat(os.path.join(directory, name))

    api.create_trace(new_key, user=username, upload_time=ts, size=stats.st_size, name=trace_name)

    return flask.redirect(flask.url_for("get_trace", trace_key=new_key, _external=True))


@app.template_filter("fromtimestamp")
def fromtimestamp(s):
    return datetime.datetime.utcfromtimestamp(s).isoformat(timespec="seconds")


@app.route("/t/<trace_key>")
def get_trace(trace_key):

    trace = api.get_trace(trace_key)
    if not trace:
        flask.abort(404)

    return render_template("trace.html.j2", trace_key=trace_key, trace=trace)


@app.route("/t/<trace_key>/download")
def download_trace(trace_key):
    if not api.get_trace(trace_key):
        flask.abort(404)

    directory, name = api.get_trace_content_path(trace_key)
    return flask.send_from_directory(directory, name)


@app.route("/t/<trace_key>/raw")
def get_trace_data(trace_key):
    if not api.get_trace(trace_key):
        flask.abort(404)

    directory, name = api.get_trace_content_path(trace_key)
    return flask.send_from_directory(directory, name)
