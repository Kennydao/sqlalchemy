import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
from flask import Flask, jsonify, request
from sqlalchemy.ext.declarative import declarative_base
import datetime as dt


#################################################
# Database Setup
#################################################

engine = create_engine('sqlite:///./Resources/hawaii.sqlite')

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Viewing all the classes
Base.classes.keys()

#Base.metadata.tables

# Save reference to the table
Measure = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available routes."""

    return (
        f"Welcome to The Climate API!<br/>"
        f"--------------------------<br/>"
        f"Available Routes:<br/>"
        f"--------------------------<br/>"
        f"  /api/v1.0/precipitation<br/>"
        f"  /api/v1.0/stations<br/>"
        f"  /api/v1.0/tobs<br/>"
        f"  /api/v1.0/temperature?start=&ltstart_date&gt&end=&ltend_date&gt"
    )

@app.route("/api/v1.0/precipitation")
def names():
    # Create session (link) from Python to the DB
    session = Session(engine)

    """Retrieving precipitation data in dataset"""
    # Query all datapoint in Measurememt
    Sel = [Measure.date, Measure.prcp]
    data = session.query(*Sel).all()

    # Close the session
    session.close()

    # Convert results to a list of dictionaries
    precip_dict = {}
    for date, precip in data:
        precip_dict[date] = precip
    precip_list = [precip_dict]

    if len(precip_list)==0 :
        return jsonify({"Error": "No Data Found"}), 404
    else:
        return jsonify(precip_list)

@app.route("/api/v1.0/stations")
def station_list():
    """ Listing all the stations available in the dataset """

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # retrieving all station available in dataset
    stations = session.query(Measure.station).distinct().all()

    # close the session
    session.close()

    # Convert results to a dictionary

    stations_list= []

    for station in stations:
        stations_dict = {}
        stations_dict["Station"] = station[0]
        stations_list.append(stations_dict)

    if len(stations_list) > 0:
        return jsonify(stations_list)
    else:
        return jsonify({"Error": "No Data Found"}), 404


@app.route("/api/v1.0/tobs")
def tobs():
    """ Displaying the dates and temperature observations of
    the most active station for the last year of data """

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # acquiring the last date in the dataset
    #Sel = ["Select date From Measure Group By date Order By date Desc"]
    last_date = session.query(func.max(Measure.date))
    last_date = last_date[0][0]

    # Calculate the date 1 year ago from the last data point
    one_yr_ago = dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # retrieving the most active station for the last year of data
    query = ["Select station, count(station) \
                From Measurement Group By station \
                Order By count(station) Desc"]
    most_active = engine.execute(*query).fetchone()
    sel_station = most_active[0]

    # retrieving data for the most active station
    data = session.query(Measure.date, Measure.tobs).\
                        filter(Measure.date >= one_yr_ago.strftime("%Y-%m-%d")).\
                        filter(Measure.date <= last_date).\
                        filter(Measure.station == sel_station).all()

    # close the session
    session.close()

    # Convert results to a dictionary
    temp_list= []

    for date in data:
        temp_dict = {}
        temp_dict['Date'] = date[0]
        temp_dict['Temp'] = date[1]
        temp_list.append(temp_dict)

    if len(temp_list) > 0:
        return (jsonify(temp_list),f"F")
        # return (jsonify(temp_list),f"F")
    else:
        return jsonify({"Error": "No Data Found"}), 404

@app.route("/api/v1.0/temperature", methods=['GET'])
def my_temp():
    """displaying min, average and max temperature for dates input
    """
    param = request.args.to_dict()

    # create session (python to db)
    session = Session(engine)

    # verifying the input parameter
    if len(param) == 0:
        return jsonify({"Error": "No Data Found"}), 404
    if len(param) == 1: # if only start_date provided
        data = session.query(Measure.date, func.min(Measure.tobs),\
                        func.round(func.avg(Measure.tobs),1),\
                        func.max(Measure.tobs)).\
                        filter(Measure.date >= param['start']).\
                        group_by(Measure.date).all()
    else: # start_date and end_date provided
        data = session.query(Measure.date, func.min(Measure.tobs),\
                        func.round(func.avg(Measure.tobs),1),\
                        func.max(Measure.tobs)).\
                        filter(Measure.date >= param['start']).\
                        filter(Measure.date <= param['end']).\
                        group_by(Measure.date).all()

    # Close the session
    session.close()

    # Convert results to a dictionary
    temp_list= []

    for date in data:
        temp_dict = {}

        temp_dict["Date"] = date[0]
        temp_dict["Min Temp"] = date[1]
        temp_dict["Avg Temp"] = date[2]
        temp_dict["Max Temp"] = date[3]
        temp_list.append(temp_dict)

    if len(temp_list) > 0:
        return jsonify(temp_list)
    else:
        return jsonify({"Error": "No Data Found"}), 404

if __name__ == '__main__':
    app.run(debug=True)