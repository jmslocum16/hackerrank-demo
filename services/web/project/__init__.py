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

def reset_data():
    count_by_url.clear()
    latency_by_url.clear()
    outstanding_by_url.clear()
    for u in backend_urls:
        outstanding_by_url[u] = 0



backend_urls=['http://web_backend:4000', 'http://web_backend2:4001', 'http://web_backend3:4002']


# async stuff
async def get_url(session, url, resource, do_stats):
    start_time = time.perf_counter()
    if (do_stats):
        count_by_url[url] += 1
        outstanding_by_url[url] += 1
    async with session.get(url + resource, ssl=False) as response:
        obj = await response.json()
        t = time.perf_counter() - start_time
        if (do_stats):
            latency_by_url[url].append(t)
            outstanding_by_url[url] -= 1
        return obj


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
def choose_url(lbalgo):
    global next_url

    if ("random" == lbalgo):
        return random.choice(backend_urls)
    elif ("roundrobin" == lbalgo):
        url = backend_urls[next_url]
        next_url = (next_url + 1) %  len(backend_urls)
        return url
    elif ("jsq" == lbalgo):
        return get_shortest_queue()
    else:
        print('invalid lbalgo ' + lbalgo)
        raise RuntimeError()

async def do_bench(rps, seconds, rwratio, lbalgo):
    write_pct = 1.0 - rwratio
    write_tasks = int(rps * seconds * write_pct)
    read_tasks = rps * seconds - write_tasks
    task_resources = ['/inc' for i in range(write_tasks)] + ['/get' for j in range (read_tasks)]
    random.shuffle(task_resources)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(rps * seconds):
            url = choose_url(lbalgo)
            # print(str(time.time()) + ") " + str(i) + ":  queue")
            tasks.append(asyncio.create_task(get_url(session, url, task_resources[i], True)))
            # TODO poisson
            await asyncio.sleep(1.0 / rps)
        await asyncio.gather(*tasks)
        cntval = await get_url(session, choose_url(lbalgo), '/get', False)
        print(cntval['counter_value'])
        return cntval['counter_value']

    
def get_latency_percentiles(latencies, percentiles):
    sl = sorted(latencies)
    if len(latencies) == 0:
        return [0.0 for p in percentiles]
    return [sl[int(len(sl) * p)] for p in percentiles]


last_valid = False
last_run_key = None

history = []

@app.route("/")
def home():
    global last_valid
    global last_run_key
    # just to get counter value
    cntval = asyncio.run(do_bench(0,0,0.5,"random"))

    pctiles = [0.5, 0.9, 0.99]
    all_latencies = []
    all_cnt = 0
    info = []
    headers = ['Server', 'Request Count', 'Median (ms)', 'P90 (ms)', 'P99 (ms)']
    for x, y in latency_by_url.items():
        server_pctiles = get_latency_percentiles(y, pctiles)
        server_cnt = count_by_url[x]
        all_cnt += server_cnt
        # serverInfo = x + ' = ' + str(server_cnt) + ': (' + ' '.join([str(x) for x in pctiles]) + '): ( ' + ' '.join(server_pctiles) + ')'
        serverInfo = [x, str(server_cnt)] + [("%.2f" % (1000.0 * p)) for p in server_pctiles]
        # print(serverInfo)
        print(' '.join(serverInfo))
        info.append(serverInfo)
        all_latencies += y
    all_pctiles = get_latency_percentiles(all_latencies, pctiles)
    # overallInfo = 'overall: = ' + str(all_cnt) + ' (' + ' '.join([str(x) for x in pctiles]) + '): ( ' + ' '.join(all_pctiles) + ')'
    overallInfo = ['Overall', str(all_cnt)] + [("%.2f" % (1000.0 * p)) for p in all_pctiles]
    print(' '.join(overallInfo))
    info = [overallInfo] + info

    if (last_valid):
        history.append([last_run_key] + overallInfo[1:])

    last_valid = False

    return render_template(
        'home.html',
        title="Demo Site",
        cntval=cntval,
        headers=headers,
        info=info,  
        history=history[::-1]
    )

@app.route("/genreq", methods=['POST'])
def genreq():
    global last_valid
    global last_run_key
    rps = int(request.form['rps'])
    runtime = int(request.form['runtime'])
    rwratio = float(request.form['rwratio'])
    lbalgo = request.form['lbalgo']

    reset_data()

    cntval = asyncio.run(do_bench(rps, runtime, rwratio, lbalgo))
    
    last_valid = True
    last_run_key = ",".join([str(rps), str(runtime), str(rwratio), lbalgo])

    return redirect(url_for('home'))

@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


