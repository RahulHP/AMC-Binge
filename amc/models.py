from amc import db


class Theatre(db.Model):
    __tablename__ = 'theatres'
    theatre_id = db.Column(db.Integer, primary_key=True)
    theatre_name = db.Column(db.String)
    postal_code = db.Column(db.String)
    market_name = db.Column(db.String)
    state = db.Column(db.String)

    def __repr__(self):
        return self.theatre_name


class ShowDate(db.Model):
    __tablename__ = 'showdates'
    theatre_id = db.Column(db.Integer, primary_key=True)
    show_date = db.Column(db.Date, primary_key=True)
    number_showtimes = db.Column(db.Integer)
    number_movies = db.Column(db.Integer)
    movie_ids = db.Column(db.String)

    def __repr__(self):
        return self.show_date


class Movie(db.Model):
    __tablename__ = 'movies'
    movie_id = db.Column(db.Integer, primary_key=True)
    movie_name = db.Column(db.String)
    sortable_movie_name = db.Column(db.String)
    api_run_time_min = db.Column(db.Integer)
    dynamic_poster_url = db.Column(db.String)
    slug = db.Column(db.String)
    mpaaRating = db.Column(db.String)
    score = db.Column(db.Float)
    synopsis = db.Column(db.String)

    def __repr__(self):
        return self.sortable_movie_name


class Showtime(db.Model):
    __tablename__ = 'showtimes'
    showtime_id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer)
    theatre_id = db.Column(db.Integer)
    show_date = db.Column(db.Date)

    movie_name = db.Column(db.String)
    sortable_movie_name = db.Column(db.String)

    official_start_time = db.Column(db.DateTime)
    predicted_start_time = db.Column(db.DateTime)
    predicted_end_time = db.Column(db.DateTime)
    showtime_runTime = db.Column(db.Integer)

    isAlmostSoldOut = db.Column(db.Boolean)
    isSoldOut = db.Column(db.Boolean)

    def __repr__(self):
        return '{name} - {start} : {end}'.format(name=self.movie_name, theatre=self.theatre_id,
                                                 start=self.official_start_time.strftime('%I:%M %p'),
                                                 end=self.predicted_end_time.strftime('%I:%M %p'))


class Result(db.Model):
    __tablename__ = 'Results'
    theatre_id = db.Column(db.Integer, primary_key=True)
    show_date = db.Column(db.Date, primary_key=True)
    showtime1_id = db.Column(db.Integer, primary_key=True)
    showtime2_id = db.Column(db.Integer, primary_key=True)
    waiting_time = db.Column(db.Integer)

    movie1_id = db.Column(db.Integer)
    movie2_id = db.Column(db.Integer)

    def __repr__(self):
        return '{m1} - {w} - {m2}'.format(m1=self.movie1_id, w=self.waiting_time, m2=self.movie2_id)
