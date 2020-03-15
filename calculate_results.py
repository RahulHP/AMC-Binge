from amc import db
from amc.models import Theatre, ShowDate, Movie, Showtime, Result
from collections import defaultdict
from datetime import date,timedelta
from itertools import permutations
from typing import List
import bisect
import logging
from logging.handlers import TimedRotatingFileHandler
import os

LOG_FILE_NAME = 'process.log'
LOG_PATH = os.path.join('logs', LOG_FILE_NAME)

THRESHOLD_MINUTES = 10

def bucket_and_sort_showtimes(theatre_id, show_date):
    showtimes = db.session.query(Showtime).filter_by(theatre_id=theatre_id).filter_by(show_date=show_date).all()
    movie_dict = defaultdict(list)
    for i in showtimes:
        movie_dict[i.movie_id].append(i)
    showtime_lookup = dict()
    for movie_id in movie_dict.keys():
        movie_dict[movie_id].sort(key=lambda x: x.predicted_start_time)
        showtime_lookup[movie_id] = [showtime.predicted_start_time for showtime in movie_dict[movie_id]]

    return movie_dict, showtime_lookup

def get_earliest_showtime_index(movie1_end_time, list_of_movie2_start_times):
    i = bisect.bisect_left(list_of_movie2_start_times, movie1_end_time)
    if i != len(list_of_movie2_start_times):
        return i
    return None


def get_results(theatre_id: int, show_date: date):
    logger.debug("Calculating Results for {id} : {date}".format(id=theatre_id, date=show_date))
    movie_buckets, showtime_lookup = bucket_and_sort_showtimes(theatre_id, show_date)
    movie_ids = list(movie_buckets.keys())
    for movie1_id, movie2_id in permutations(movie_ids, 2):
        movie1_showtimes = movie_buckets[movie1_id]
        movie2_showtimes = movie_buckets[movie2_id]
        movie2_showtimes_lookup = showtime_lookup[movie2_id]
        for first_show in movie1_showtimes:
            next_showtime_index = get_earliest_showtime_index(first_show.predicted_end_time, movie2_showtimes_lookup)
            if next_showtime_index:
                next_showtime = movie2_showtimes[next_showtime_index]
                waiting = next_showtime.predicted_start_time - first_show.predicted_end_time
                if waiting.seconds / 60 <= THRESHOLD_MINUTES:
                    logger.debug("Result Found : {movie1_id} : {showtime1_id} - {movie2_id} : {showtime2_id}"
                                 .format(movie1_id=first_show.movie_id, movie2_id=next_showtime.movie_id,
                                         showtime1_id=first_show.showtime_id, showtime2_id=next_showtime.showtime_id))
                    r = Result(theatre_id=theatre_id, show_date=show_date,
                               movie1_id=movie1_id, showtime1_id=first_show.showtime_id,
                               movie2_id=movie2_id, showtime2_id=next_showtime.showtime_id,
                               waiting_time=waiting.seconds/60)
                    db.session.add(r)
    db.session.commit()

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = TimedRotatingFileHandler(LOG_PATH, when='d', interval=1, backupCount=14)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    theatre_ids = [x[0] for x in db.session.query(Theatre.theatre_id).all()]
    show_dates = [x[0] for x in db.session.query(ShowDate.show_date).all()]

    for t_id in theatre_ids:
        for s_date in show_dates:
            get_results(t_id, s_date)
