import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread': False})

# Reflect an existing database into a new model
Base = automap_base()
# Reflect the tables
Base.prepare(engine, reflect=True)

# Save references to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)


#################################################
# Date List Setup
#################################################

# Setup a list of dates for user date searches
date_results = session.query(Measurement.date).distinct().all()
dates_list = [record_date.date for record_date in date_results]


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"<br/>"
        f"---Check the precipitation for all dates in the database---<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"<br/>"
        f"---Check the information about all the stations---<br/>"
        f"/api/v1.0/stations<br/>"
        f"<br/>"
        f"---Check the temperature observations from a year from the last data point---<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>"
        f"---Get the minimum temperature, the average temperature, and the max temperature dates ranging from a given start date to the most recent date data point---<br/>"
        f"---Input start_date (format: YYYY/MM/DD) for variable 'start' after /api/v1.0/---<br/>"
        f"/api/v1.0/start<br/>" 
        f"<br/>"
        f"---Get the minimum temperature, the average temperature, and the max temperature for a given start-end range---<br/>"
        f"---Input start_date/end_date (format: YYYY/MM/DD) for variables 'start' and 'end' after /api/v1.0/---<br/>"
        f"/api/v1.0/start/end"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
 
    """Convert the query results to a Dictionary using `date` as the key and `prcp` as the value."""
    # Query date and precipitation
    results = session.query(Measurement.date, Measurement.prcp).all()
    
    # Create a dictionary from the row data and append to a list of all_precipitation
    all_precipitation = []
    for precipitation in results:
        precipitation_dict = {}
        precipitation_dict[precipitation.date] = precipitation.prcp
        all_precipitation.append(precipitation_dict)

    # Return precipitation information for dates
    return jsonify(all_precipitation)


@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Query all stations
    results = session.query(Station).all()

    # Create a dictionary from the row data and append to a list of all_stations
    all_stations = []
    for station in results:
        station_dict = {}
        station_dict["station"] = station.station
        station_dict["latitude"] = station.latitude
        station_dict["longitude"] = station.longitude
        station_dict["elevation"] = station.elevation
        all_stations.append(station_dict)

    # Return information for all stations
    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    """Query for the dates and temperature observations from a year from the last data point."""
    # Get date from last data point
    tobs_recent_date_query = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    tobs_recent_date_list = list(np.ravel(tobs_recent_date_query))
    tobs_recent_date = dt.datetime.strptime(tobs_recent_date_list[0], "%Y-%m-%d").date()

    # Get date from a year from the last data point date
    tobs_year_ago = tobs_recent_date - dt.timedelta(days=365)

    # Query dates and temperature observations from a year from the last data point
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= tobs_year_ago).\
        filter(Measurement.date <= tobs_recent_date).\
        order_by(Measurement.date.desc()).all()

    # Create a dictionary from the row data and append to a list of all_tobs
    all_tobs = []
    for tobs in results:
        tobs_dict = {}
        tobs_dict["date"] = tobs.date
        tobs_dict["tobs"] = tobs.tobs
        all_tobs.append(tobs_dict)
    
    # Return dates and temperature observations
    return jsonify(all_tobs)


@app.route("/api/v1.0/<start>")
def tempstats_start(start):
    '''Return a JSON list of the minimum temperature, the average temperature, and the max temperature for dates ranging from a given start date
        to the most recent date data point, or a 404 if the given start date is not found'''

    if start in dates_list: 

        # Query minimum temperature, the average temperature, and the max temperature for dates ranging from a given start date
        # to the most recent date data point
        sel = [Measurement.date, 
            func.min(Measurement.tobs).label("TMIN"),
            func.avg(Measurement.tobs).label("TAVG"),
            func.max(Measurement.tobs).label("TMAX")]
        results = session.query(*sel).filter(Measurement.date >= start).group_by(Measurement.date).all()
        
        # Create a dictionary from the row data and append to a list of all_temp_stats
        all_temp_stats = []
        for temp_stats in results:
            temp_stats_dict = {}
            temp_stats_dict["date"] = temp_stats.date
            temp_stats_dict["TMIN"] = temp_stats.TMIN
            temp_stats_dict["TAVG"] = temp_stats.TAVG
            temp_stats_dict["TMAX"] = temp_stats.TMAX
            all_temp_stats.append(temp_stats_dict)
    
        # Return dates and temperature stats
        return jsonify(all_temp_stats)

    else:
        return jsonify({"error": f"Date with start_date {start} not found. Date format must be YYYY-MM-DD."}), 404


@app.route("/api/v1.0/<start>/<end>")
def tempstats_start_end(start, end):
    '''Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start-end range.'''

    if start in dates_list and end in dates_list: 

        # Query minimum temperature, the average temperature, and the max temperature for a given start-end range
        sel = [Measurement.date, 
            func.min(Measurement.tobs).label("TMIN"),
            func.avg(Measurement.tobs).label("TAVG"),
            func.max(Measurement.tobs).label("TMAX")]
        results = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).group_by(Measurement.date).all()
        
        # Create a dictionary from the row data and append to a list of all_temp_stats
        all_temp_stats = []
        for temp_stats in results:
            temp_stats_dict = {}
            temp_stats_dict["date"] = temp_stats.date
            temp_stats_dict["TMIN"] = temp_stats.TMIN
            temp_stats_dict["TAVG"] = temp_stats.TAVG
            temp_stats_dict["TMAX"] = temp_stats.TMAX
            all_temp_stats.append(temp_stats_dict)
    
        # Return dates and temperature stats
        return jsonify(all_temp_stats)

    elif start not in dates_list and end in dates_list:

        # Return error message if start date is not found
        return jsonify({"error": f"Date with start_date {start} not found. Date format must be YYYY-MM-DD."}), 404

    elif start in dates_list and end not in dates_list:

        # Return error message if end date is not found
        return jsonify({"error": f"Date with end_date {end} not found. Date format must be YYYY-MM-DD."}), 404

    else:

        # Return error message if start date and end date are not found
        return jsonify({"error": f"Date with start_date {start} and end_date {end} not found. Date format must be YYYY-MM-DD."}), 404


if __name__ == '__main__':
    app.run(debug=True)
