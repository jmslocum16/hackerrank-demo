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
outstanding_by_url = defaultdict(int)
backend_urls=['http://web_backend:4000', 'http://web_backend2:4001', 'http://web_backend3:4002']


# async stuff
async def get_url(session, url, resource, i):
    print(str(time.time()) + ") " + str(i) + ":  start")
    start_time = time.perf_counter()
    count_by_url[url] += 1
    outstanding_by_url[url] += 1
    async with session.get(url + resource, ssl=False) as response:
        print(str(time.time()) + ") " + str(i) + ":  sent")
        obj = await response.json()
        print(str(time.time()) + ") " + str(i) + ":  done")
        print(obj)
        t = time.perf_counter() - start_time
        latency_by_url[url].append(t)
        outstanding_by_url[url] -= 1
        return obj


for u in backend_urls:
    outstanding_by_url[u] = 0

def get_shortest_queue():
    min_v = 100000000
    min_results = []
    for k, v in outstanding_by_url.items():
        if v <= min_v:
            if v < min_v:
                min_results = []
                min_v = v
            min_results.append(k)
    print('min oustanding: ' + str(min_v))
    return random.choice(min_results)

next_url = 0
def choose_url():
    global next_url
    # TODO load balance?
    # random
    # return random.choice(backend_urls)

    # round robin
    #url = backend_urls[next_url]
    #next_url = (next_url + 1) %  len(backend_urls)
    #return url

    # shortest queue
    return get_shortest_queue()

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

"""
async def do_bench():
    async with aiohttp.ClientSession() as session:   
        tasks = [get_url(session, choose_url(), '/inc') for i in range(100)]
        await asyncio.gather(*tasks)
        cntval = await get_url(session, choose_url(), '/get')
        print(cntval['counter_value'])
        return cntval['counter_value']
"""
async def do_bench(rps, seconds):
    write_pct = 0.2
    write_tasks = int(rps * seconds * write_pct)
    read_tasks = rps * seconds - write_tasks
    task_resources = ['/inc' for i in range(write_tasks)] + ['/get' for j in range (read_tasks)]
    random.shuffle(task_resources)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(rps * seconds):
            url = choose_url()
            print(str(time.time()) + ") " + str(i) + ":  queue")
            tasks.append(asyncio.create_task(get_url(session, url, task_resources[i], i)))
            # TODO poisson
            await asyncio.sleep(1.0 / rps)
        await asyncio.gather(*tasks)
        cntval = await get_url(session, choose_url(), '/get', 100000)
        print(cntval['counter_value'])
        return cntval['counter_value']

    
def get_latency_percentiles(latencies, percentiles):
    sl = sorted(latencies)
    return [str(sl[int(len(sl) * p)]) for p in percentiles]

@app.route("/")
def home():
    # inc_counter()
    # cntval = get_counter()
    cntval = asyncio.run(do_bench(1000, 5))
    # print(str(latency_by_url))
    pctiles = [0.5, 0.9, 0.99]
    all_latencies = []
    all_cnt = 0
    for x, y in latency_by_url.items():
        server_pctiles = get_latency_percentiles(y, pctiles)
        server_cnt = count_by_url[x]
        all_cnt += server_cnt
        print(x + ' = ' + str(server_cnt) + ': (' + ' '.join([str(x) for x in pctiles]) + '): ( ' + ' '.join(server_pctiles) + ')')
        all_latencies += y
    all_pctiles = get_latency_percentiles(all_latencies, pctiles)
    print('overall: = ' + str(all_cnt) + ' (' + ' '.join([str(x) for x in pctiles]) + '): ( ' + ' '.join(all_pctiles) + ')')
    
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


