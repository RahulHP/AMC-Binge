from amc import db
from amc.models import Theatre, ShowDate, Movie, Showtime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
LOG_FILE_NAME = 'clean.log'
LOG_PATH = os.path.join('logs', LOG_FILE_NAME)

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = TimedRotatingFileHandler(LOG_PATH, when='d', interval=1, backupCount=14)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("Deleting Theatres")
    db.session.query(Theatre).delete()

    logger.info("Deleting ShowDates")
    db.session.query(ShowDate).delete()

    logger.info("Deleting Movies")
    db.session.query(Movie).delete()

    logger.info("Deleting Showtimes")
    db.session.query(Showtime).delete()

    db.session.commit()
