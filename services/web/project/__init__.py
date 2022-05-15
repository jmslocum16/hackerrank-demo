import os
import psycopg2
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


