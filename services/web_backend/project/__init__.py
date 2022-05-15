import os
import psycopg2
from flask import (
    Flask,
    request,
    jsonify
)

app = Flask(__name__)
app.config.from_object("project.config.Config")

conn = psycopg2.connect("dbname=counters host=db port=5432  user=test_app password=test_app")
# testing
cur = conn.cursor()
cur.execute('SELECT version()')

# display the PostgreSQL database server version
db_version = cur.fetchone()
print(db_version)

cur.close()


def get_counter():
    cur = conn.cursor()
    cur.execute('SELECT countvalue FROM counters WHERE ID=1')
    cntval = cur.fetchone()[0]
    print(cntval)
    cur.close()
    return cntval

def inc_counter():
    cur = conn.cursor()
    cur.execute('UPDATE counters SET countvalue = countvalue + 1 WHERE ID=1')
    conn.commit()
    cur.close()

@app.route("/get")
def get_counter_req():
    cntval = get_counter()
    return jsonify(counter_value=cntval);


@app.route("/inc", methods=['POST'])
def inc_counter_req():
    inc_counter()
    return jsonify(success="true")
