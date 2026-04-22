import sqlite3
from datetime import datetime

DATABASE = 'readings.db'

# Differential threshold in °F
HEAT_DIFFERENTIAL = 5.0

# Smoothing window
SMOOTH_WINDOW = 3

# Alert range in °F
TEMP_MIN = 65.0
TEMP_MAX = 85.0


def celsius_to_fahrenheit(c):
    return c * 9.0 / 5.0 + 32.0


def get_recent_readings(sensor_id, limit=10):
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        'SELECT temperature, humidity, timestamp FROM readings '
        'WHERE sensor_id = ? ORDER BY timestamp DESC LIMIT ?',
        (sensor_id, limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def smooth(readings):
    """Rolling average over last SMOOTH_WINDOW readings, returned in °F."""
    if not readings:
        return None
    window = readings[:SMOOTH_WINDOW]
    avg_c = sum(r['temperature'] for r in window) / len(window)
    return celsius_to_fahrenheit(avg_c)


def rate_of_change(readings):
    """°F per minute between oldest and newest reading in window."""
    if len(readings) < 2:
        return None

    newest = readings[0]
    oldest = readings[-1]

    try:
        t1 = datetime.fromisoformat(newest['timestamp'])
        t0 = datetime.fromisoformat(oldest['timestamp'])
    except ValueError:
        return None

    minutes = (t1 - t0).total_seconds() / 60.0
    if minutes == 0:
        return None

    delta_f = celsius_to_fahrenheit(newest['temperature']) - celsius_to_fahrenheit(oldest['temperature'])
    return delta_f / minutes


def infer_hvac_state(upstairs_smooth, downstairs_smooth):
    """
    Infer HVAC state from floor differential.
    If upstairs is more than HEAT_DIFFERENTIAL°F warmer -> heat is on.
    """
    if upstairs_smooth is None or downstairs_smooth is None:
        return 'unknown'
    diff = upstairs_smooth - downstairs_smooth
    if diff >= HEAT_DIFFERENTIAL:
        return 'heating'
    return 'idle'


def check_alert(smoothed_temp, sensor_id):
    """Alert if temp is out of comfortable range."""
    if smoothed_temp is None:
        return None
    if smoothed_temp < TEMP_MIN:
        return f"{sensor_id} too cold: {smoothed_temp:.1f}°F (min {TEMP_MIN}°F)"
    if smoothed_temp > TEMP_MAX:
        return f"{sensor_id} too hot: {smoothed_temp:.1f}°F (max {TEMP_MAX}°F)"
    return None


def analyze():
    """
    Full pipeline:
      raw readings -> smooth -> differential -> HVAC inference -> alerts
    """
    up_readings = get_recent_readings('upstairs')
    down_readings = get_recent_readings('downstairs')

    up_smooth = smooth(up_readings)
    down_smooth = smooth(down_readings)

    up_rate = rate_of_change(up_readings)
    down_rate = rate_of_change(down_readings)

    differential = (up_smooth - down_smooth) if (up_smooth and down_smooth) else None
    hvac = infer_hvac_state(up_smooth, down_smooth)

    alerts = []
    a = check_alert(up_smooth, 'upstairs')
    if a:
        alerts.append(a)
    a = check_alert(down_smooth, 'downstairs')
    if a:
        alerts.append(a)

    return {
        'upstairs': {
            'smoothed_temp': up_smooth,
            'rate_of_change': up_rate,
        },
        'downstairs': {
            'smoothed_temp': down_smooth,
            'rate_of_change': down_rate,
        },
        'differential': differential,
        'hvac_state': hvac,
        'alerts': alerts,
    }
