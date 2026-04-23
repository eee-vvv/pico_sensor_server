# Pico Temperature Sensor Server-Side Code

## Setup

All you need to do to set this up is make sure you have the appropriate packages installed via pip (I did so inside a virtual environment), then run app.py.

## What it does

This code is also quite simple; the bulk of it is made up of 3 major files, `app.py`, `pipeline.py`, and `templates/index.html`, with some JS in `static/script.js`.

`app.py` is a very simple Flask setup: the only packages it imports are sqlite to maintain a super simple database of temperature reading that can persist on disk, pytz to convert from UTC to Eastern Time, and flask, to run the REST API. There are a few simple helper functions (for example, init_db is a basic SQL query that makes sure the table exists and sets the fields of a database entry: id, sensor_id, temperature, humidity, and a timestamp.

There are 3 routes in the API:
- `/reading`, which only takes POST requests. It receives the readings from the Raspberry Pi Picos (though any device could send it data in the correct format), inserts the data into the database, does some logging, and sends a status code back.
- `/pipeline`, which takes GET requests. This one is not used directly in the application, but is useful for demo purposes, as it returns the output of the data processing pipeline in json form.
- `/`, which is where the web interface lives. It populates a map with the latest temperature and humidity readings from each sensor, a list with the 100 most recent readings, runs the data through the pipeline, and then passes that into the index.html template.

- `pipeline.py` contains all the data processing. It is ultimately quite simple right now. It does three major kinds of data processing:
- 1. it "smooths" the 3 most recent readings into an average, giving the data a bit more stability.
  2. it takes those smoothed readings and calculates the difference between upstairs and downstairs.
  3. Using that smoothed differential, it attempts to determine if the heater is turned on.
 
  Lastly, `pipeline.py` also creates alerts if the temperature both upstairs and downstairs falls outside of a predetermined range.

  `index.html` is more self-explanatory - it displays a static website (you must refresh to get new data), with some simple JS, that shows the current temperature upstairs and downstairs, a chart of the temperature change over time, and any alerts there might be for the temperature going out of the appropriate range.
