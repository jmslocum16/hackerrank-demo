import os
import requests
import json
import random
from collections import defaultdict
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

count_by_url = defaultdict(int)
#backend_urls=['http://web_backend', 'http://web_backend2', 'http://web_backend3']
backend_urls=['http://web_backend']
backend_port=4000

def choose_url():
    # TODO load balance?
    return random.choice(backend_urls)

def get_url(resource):
    backend_url = choose_url()
    count_by_url[backend_url] += 1
    return backend_url + ':' + str(backend_port) + resource

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
        cntval=cntval,
        cntByUrl=count_by_url
    )

@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


