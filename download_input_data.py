import dateutil.parser
from amc import db
from amc.models import Theatre, ShowDate, Movie, Showtime
from sqlalchemy import func, distinct
import requests
import dateutil.parser
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from config import AMC
from datetime import date,timedelta
from typing import List


api_key = AMC.SECRET_KEY
LOG_FILE_NAME = 'download.log'
LOG_PATH = os.path.join('logs', LOG_FILE_NAME)


def get_theatre_data(theatre_id:int):
    logger.debug("Getting Theatre : {id}".format(id=theatre_id))
    API_URL = 'http://api.amctheatres.com/v2/theatres/{id}'
    request_url = API_URL.format(id=theatre_id)
    r = requests.get(request_url, headers={'X-AMC-Vendor-Key': api_key})
    response_json = r.json()
    t = Theatre(theatre_id=theatre_id, theatre_name=response_json['name'],
                postal_code=response_json['location']['postalCode'],
                market_name=response_json['location']['marketName'],
                state=response_json['location']['stateName'])
    return t


def get_all_theatres(theatre_ids: List[int]):
    for t_id in theatre_ids:
        theatre = get_theatre_data(t_id)
        db.session.add(theatre)
    db.session.commit()


def get_showtimes(theatre_id: int, show_date: date):
    logger.debug("Getting Showtimes : {id} - {date}".format(id=theatre_id, date=date))
    API_URL = 'http://api.amctheatres.com/v2/theatres/{theatreNumber}/showtimes/{date}'
    request_url = API_URL.format(theatreNumber=theatre_id, date=show_date.strftime("%m-%d-%y"))
    r = requests.get(request_url, headers={'X-AMC-Vendor-Key': api_key}, params={'page-size': 150,
                                                                                      'exclude-attributes': 'NOALIST'})
    showtimes_json = r.json()['_embedded']['showtimes']
    for i in showtimes_json:
        showtime_datetime = dateutil.parser.isoparse(i['showDateTimeLocal'])
        showtime_date = showtime_datetime.date()
        logger.debug("Adding Showtime : {id} - {start_time}".format(id=i['id'], start_time=showtime_datetime))
        s = Showtime(showtime_id=i['id'], movie_id=i['movieId'], theatre_id=i['theatreId'], show_date=showtime_date,
                     movie_name=i['movieName'], sortable_movie_name=i['sortableMovieName'],
                     official_start_time=showtime_datetime,
                     predicted_start_time=showtime_datetime+timedelta(minutes=20),
                     predicted_end_time=showtime_datetime+timedelta(minutes=20+i['runTime']),
                     showtime_runTime=i['runTime'], isSoldOut=i['isSoldOut'], isAlmostSoldOut=i['isAlmostSoldOut'])
        db.session.add(s)
    db.session.commit()


def get_all_movie_ids():
    movie_ids = [x[0] for x in db.session.query(Showtime.movie_id).distinct().all()]
    print(movie_ids)
    return movie_ids


def get_showtimes_for_range(theatre_id: int, start_date: date, num_days: int):
    for i in range(num_days):
        get_showtimes(theatre_id=theatre_id, show_date=start_date+timedelta(days=i))


def get_movie_data(movie_id: int):
    logger.debug("Getting Movie : {id}".format(id=movie_id))
    API_URL = 'http://api.amctheatres.com/v2/movies/{id}'
    request_url = API_URL.format(id=movie_id)
    r = requests.get(request_url, headers={'X-AMC-Vendor-Key': api_key})
    response_json = r.json()
    m = Movie(movie_id=movie_id, movie_name=response_json['name'], sortable_movie_name=response_json['sortableName'],
              api_run_time_min=response_json['runTime'],
              dynamic_poster_url=response_json['media']['posterDynamic'],
              slug=response_json['slug'], mpaaRating=response_json['mpaaRating'],
              score=response_json['score'],
              synopsis=response_json['synopsis'])
    return m


def get_all_movies(movie_ids: List[int]):
    for m_id in movie_ids:
        movie = get_movie_data(m_id)
        db.session.add(movie)
    db.session.commit()


def calculate_showdate_stats():
    calculated_results = db.session.query(Showtime.theatre_id,
                                          Showtime.show_date,
                                          func.count(Showtime.showtime_id),
                                          func.count(distinct(Showtime.movie_id)),
                                          func.group_concat(distinct(Showtime.movie_id)))\
        .group_by(Showtime.theatre_id, Showtime.show_date).all()
    column_names = ['theatre_id', 'show_date', 'number_showtimes', 'number_movies', 'movie_ids']
    showdate_objects = [ShowDate(**dict(zip(column_names, x))) for x in calculated_results]
    db.session.add_all(showdate_objects)
    db.session.commit()

def get_main_poster_url(movie_id):
    MEDIA_URL = "http://api.amctheatres.com/v2/media/movies/{id}/images"
    logger.debug("Getting Movie : {id}".format(id=movie_id))
    api_media_url = MEDIA_URL.format(id=movie_id)
    r = requests.get(api_media_url, headers={'X-AMC-Vendor-Key': api_key}, params={'content_type': 'PosterDynamic'})
    if r.json()['count'] == 0:
        logger.error("No movie posters found : {id}".format(id=movie_id))
        return None
    try:
        poster_url = r.json()['_embedded']['media'][0]['_embedded']['renditions'][0]['url']
        return poster_url
    except KeyError:
        logger.error("Error downloading movie poster : {id}".format(id=movie_id))
        return None


def get_format_poster_url(main_url: str):
    cloudinary_url = "https://amc-theatres-res.cloudinary.com/"
    path = main_url.split(cloudinary_url, maxsplit=1)[1]
    image_formatting_options = "c_thumb,f_auto,fl_preserve_transparency,g_face,h_120,q_auto,r_max,w_120"
    image_formatting_url = "{cloudinary}/image/upload/{opts}/e_trim/{path}"\
        .format(cloudinary=cloudinary_url, opts=image_formatting_options, path=path)
    return image_formatting_url


def download_image(url, local_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)


def download_movie_poster(movie_id):
    main_poster_url = get_main_poster_url(movie_id)
    if main_poster_url:
        format_poster_url = get_format_poster_url(main_poster_url)
        file_path = os.path.join('/home/ubuntu/amcv2/amc', 'static', 'img', '{id}.png'.format(id=movie_id))
        download_image(format_poster_url, file_path)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = TimedRotatingFileHandler(LOG_PATH, when='d', interval=1, backupCount=14)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    theatre_file = 'theatres.txt'
    date_query_range = 4

    with open(theatre_file, 'r') as fp:
        theatres_str = fp.read().splitlines()
    theatres = [int(x) for x in theatres_str]
    print(theatres)

    get_all_theatres(theatres)

    for theatre_id in theatres:
        get_showtimes_for_range(theatre_id, date.today(), date_query_range)

    movie_ids = get_all_movie_ids()

    get_all_movies(movie_ids)

    calculate_showdate_stats()

    for movie_id in movie_ids:
        print(movie_id)
        download_movie_poster(movie_id)
