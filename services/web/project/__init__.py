import os
import requests
import json
from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    redirect,
    url_for,
    render_template
)

app = Flask(__name__)
app.config.from_object("project.config.Config")

backend_url='http://web_backend'
backend_ports=[4000]

def choose_port():
    # TODO load balance?
    return backend_ports[0]

def get_url(resource):
    return backend_url + ':' + str(choose_port()) + resource

def get_counter():
    result = requests.get(get_url('/get'))
    print(result.text)
    cntval = int(json.loads(result.text)['counter_value'])
    print(str(cntval))
    return cntval
    
def inc_counter():
    result = requests.post(get_url('/inc'))
    print(result.text)

@app.route("/")
def home():
    inc_counter()
    cntval = get_counter()
    return render_template(
        'home.html',
        title="Demo Site",
        cntval=cntval
    )

@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


