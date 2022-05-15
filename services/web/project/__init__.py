import os
import requests
import json
import random
from collections import defaultdict
import time
import asyncio
import aiohttp
import nest_asyncio
from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    redirect,
    url_for,
    render_template
)

nest_asyncio.apply()

app = Flask(__name__)
app.config.from_object("project.config.Config")

count_by_url = defaultdict(int)
latency_by_url = defaultdict(list)
backend_urls=['http://web_backend:4000', 'http://web_backend2:4001', 'http://web_backend3:4002']

#conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
#session = aiohttp.ClientSession(connector=conn)

# async stuff
async def get_url(session, url, resource):
    start_time = time.perf_counter()
    async with session.get(url + resource, ssl=False) as response:
        obj = await response.json()
        print(obj)
        t = time.perf_counter() - start_time
        latency_by_url[url].append(t)
        return obj

def choose_url():
    # TODO load balance?
    return random.choice(backend_urls)

def make_url(resource):
    backend_url = choose_url()
    count_by_url[backend_url] += 1
    return backend_url + resource

"""
def get_counter():
    result = requests.get(make_url('/get'))
    print(result.text)
    cntval = int(json.loads(result.text)['counter_value'])
    print(str(cntval))
    return cntval
    
def inc_counter():
    result = requests.post(make_url('/inc'))
    print(result.text)
"""

async def do_bench():
    async with aiohttp.ClientSession() as session:   
        tasks = [get_url(session, choose_url(), '/inc') for i in range(100)]
        await asyncio.gather(*tasks)
        cntval = await get_url(session, choose_url(), '/get')
        print(cntval['counter_value'])
        return cntval['counter_value']
    
def get_latency_percentiles(latencies, percentiles):
    sl = sorted(latencies)
    return [str(sl[int(len(sl) * p)]) for p in percentiles]

@app.route("/")
def home():
    # inc_counter()
    # cntval = get_counter()
    cntval = asyncio.run(do_bench())
    # print(str(latency_by_url))
    pctiles = [0.5, 0.9, 0.99]
    all_latencies = []
    for x, y in latency_by_url.items():
        server_pctiles = get_latency_percentiles(y, pctiles)
        print(x + ': (' + ' '.join([str(x) for x in pctiles]) + '): ( ' + ' '.join(server_pctiles) + ')')
        all_latencies += y
    all_pctiles = get_latency_percentiles(all_latencies, pctiles)
    print('overall: (' + ' '.join([str(x) for x in pctiles]) + '): ( ' + ' '.join(all_pctiles) + ')')
    
    return render_template(
        'home.html',
        title="Demo Site",
        cntval=cntval,
        cntByUrl=count_by_url
    )


@app.route("/genreq", methods=['POST'])
def genreq():
    # TODO DO ASYNC STUFF HERE
    pass    

@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


