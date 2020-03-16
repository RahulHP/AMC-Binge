import os
from flask import Flask,render_template, redirect, request, url_for
from config import Config
from collections import defaultdict
from datetime import date, timedelta, datetime
from sqlalchemy.orm import aliased
app = Flask(__name__)
app.config.from_object(Config)
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from amc.models import Theatre, ShowDate, Movie, Showtime, Result


@app.route('/', methods=['GET', 'POST'])
def select_theatre():
    if request.method == 'GET':
        theatres = db.session.query(Theatre).all()
        theatre_dict = defaultdict(list)
        for i in theatres:
            theatre_dict[i.state].append(i)
        return render_template('theatres.html', theatres=theatre_dict)
    else:
        return redirect(url_for('select_date', theatre_id=request.form.get('theatre_id')))


@app.route('/<theatre_id>', methods=['GET', 'POST'])
def select_date(theatre_id):
    if request.method == 'GET':
        selected_theatre = db.session.query(Theatre).filter_by(theatre_id=theatre_id).one()
        show_dates = db.session.query(ShowDate).filter_by(theatre_id=theatre_id).all()
        return render_template('dates.html', selected_theatre=selected_theatre, show_dates=show_dates)
    else:
        return redirect(url_for('select_movies', theatre_id=theatre_id, show_date=request.form.get('show_date')))


@app.route('/<theatre_id>/<show_date>', methods=['GET', 'POST'])
def select_movies(theatre_id, show_date):
    if request.method == 'GET':
        selected_theatre = db.session.query(Theatre).filter_by(theatre_id=theatre_id).one()
        show_date_dt = datetime.strptime(show_date, '%d-%m-%Y').date()
        selected_showdate = db.session.query(ShowDate).filter_by(theatre_id=theatre_id).filter_by(show_date=show_date_dt).one()
        movie_ids = selected_showdate.movie_ids.split(',')
        movies = db.session.query(Movie).filter(Movie.movie_id.in_(movie_ids)).all()
        return render_template('movies.html', selected_theatre = selected_theatre,
                               selected_showdate = selected_showdate, movies = movies)
    else:
        selected_movie_ids = [int(x) for x in request.form.get('movies').split('|')]
        show_date = datetime.strptime(show_date, '%d-%m-%Y').date()
        selected_theatre = db.session.query(Theatre).filter_by(theatre_id=theatre_id).one()
        selected_showdate = db.session.query(ShowDate).filter_by(theatre_id=theatre_id).filter_by(
            show_date=show_date).one()
        s1 = aliased(Showtime)
        s2 = aliased(Showtime)
        r = aliased(Result)
        view_results = db.session.query(r, s1, s2)\
            .filter(r.theatre_id == theatre_id)\
            .filter(r.show_date == show_date)\
            .filter(r.movie1_id.in_(selected_movie_ids))\
            .filter(r.movie2_id.in_(selected_movie_ids))\
            .filter(r.showtime1_id == s1.showtime_id)\
            .filter(r.showtime2_id == s2.showtime_id)\
            .order_by(s1.official_start_time)\
            .all()
        return render_template('results.html', selected_theatre=selected_theatre, selected_showdate=selected_showdate,
                               selected_movie_ids = selected_movie_ids, results = view_results)