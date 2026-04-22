import sqlite3
from datetime import datetime
import pytz
from flask import Flask, g, jsonify, render_template, request
from pipeline import analyze

app = Flask(__name__)
DATABASE = 'readings.db'

eastern = pytz.timezone('America/New_York')


def to_eastern(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str)
        dt = pytz.utc.localize(dt)
        return dt.astimezone(eastern).strftime('%Y-%m-%d %I:%M:%S %p')
    except:
        return ts_str


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()
    db.close()


def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0


@app.route('/reading', methods=['POST'])
def reading():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'no data'}), 400

    db = get_db()
    db.execute(
        'INSERT INTO readings (sensor_id, temperature, humidity) VALUES (?, ?, ?)',
        (data['sensor_id'], data['temperature'], data['humidity'])
    )
    db.commit()

    print(f"[{datetime.now()}] {data}")
    return jsonify({'status': 'ok'}), 200


@app.route('/pipeline')
def pipeline():
    return jsonify(analyze())


@app.route('/')
def index():
    db = get_db()

    latest = {}
    for row in db.execute(
        'SELECT sensor_id, temperature, humidity, timestamp '
        'FROM readings r1 WHERE timestamp = '
        '(SELECT MAX(timestamp) FROM readings r2 WHERE r2.sensor_id = r1.sensor_id)'
    ):
        d = dict(row)
        d['temperature'] = c_to_f(d['temperature'])
        d['timestamp'] = to_eastern(d['timestamp'])
        latest[row['sensor_id']] = d

    history = db.execute(
        'SELECT sensor_id, temperature, humidity, timestamp '
        'FROM readings ORDER BY timestamp DESC LIMIT 100'
    ).fetchall()

    history_f = []
    for r in history:
