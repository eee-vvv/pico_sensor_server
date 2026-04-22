import sqlite3
from datetime import datetime
from flask import Flask, g, jsonify, render_template, request

app = Flask(__name__)
DATABASE = 'readings.db'

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

@app.route('/')
def index():
    db = get_db()

    latest = {}
    for row in db.execute(
        'SELECT sensor_id, temperature, humidity, timestamp '
        'FROM readings r1 WHERE timestamp = '
        '(SELECT MAX(timestamp) FROM readings r2 WHERE r2.sensor_id = r1.sensor_id)'
    ):
        latest[row['sensor_id']] = dict(row)

    history = db.execute(
        'SELECT sensor_id, temperature, humidity, timestamp '
        'FROM readings ORDER BY timestamp DESC LIMIT 100'
    ).fetchall()

    return render_template('index.html', latest=latest, history=[dict(r) for r in history])

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
