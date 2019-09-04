"""
Created on: 2019-08-22 10:47:21

@Author: Rudolf De Geijter
"""

import functools
import json
import logging
from datetime import datetime
import time
import sys

import requests
import structlog
import yaml
from requests.auth import HTTPBasicAuth

from database import db_session
from models import MediaObject

# logger configuration
logging.basicConfig(format="%(message)s", level=logging.INFO, stream=sys.stdout)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,  # First step, filter by level to
        structlog.stdlib.add_logger_name,  # module name
        structlog.stdlib.add_log_level,  # log level
        structlog.stdlib.PositionalArgumentsFormatter(),  # % formatting
        structlog.processors.StackInfoRenderer(),  # adds stack if stack_info=True
        structlog.processors.format_exc_info,  # Formats exc_info
        structlog.processors.UnicodeDecoder(),  # Decodes all bytes in dict to unicode
        structlog.processors.TimeStamper(
            fmt="iso"
        ),  # Because timestamps! UTC by default
        structlog.stdlib.render_to_log_kwargs,  # Preps for logging call
        structlog.processors.JSONRenderer(),  # to json
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()

fileHandler = logging.FileHandler("{0}/{1}.log".format(".", "metadata_updater"))
log.addHandler(fileHandler)

# Load config file
DEFAULT_CFG_FILE = "./config.yml"
with open(DEFAULT_CFG_FILE, "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

token = ""


def authenticate(func):
    """Gets new token if no token"""

    @functools.wraps(func)
    def wrapper_authenticate(*args, **kwargs):
        global token
        if not token:
            token = get_token()
        return func(*args, **kwargs)

    return wrapper_authenticate


def get_token():
    user = cfg["environment"]["mediahaven"]["username"]
    password = cfg["environment"]["mediahaven"]["password"]
    url = cfg["environment"]["mediahaven"]["host"] + "/oauth/access_token"
    payload = {"grant_type": "password"}

    try:
        r = requests.post(
            url,
            auth=HTTPBasicAuth(user.encode("utf-8"), password.encode("utf-8")),
            data=payload,
        )

        if r.status_code != 201:
            raise ConnectionError(f"Failed get a token. Status: {r.status_code}")
        rtoken = r.json()["access_token"]
        token = "Bearer " + rtoken
    except Exception as e:
        log.critical(str(e))
        return None
    return token


@authenticate
def get_fragments(offset=0):
    """gets 100 fragments at a time for a configured media type

    Keyword Arguments:
        offset {int} -- offset for paging (default: {0})

    Returns:
        Dict -- contains the fragments and the total number of results
    """
    url = (
        cfg["environment"]["mediahaven"]["host"]
        + f'/media/?q=%2b(type_viaa:"{cfg["media_type"]}")\
        &startIndex={offset}&nrOfResults=100'
    )
    headers = {"Authorization": token, "Accept": "application/vnd.mediahaven.v2+json"}
    response = requests.get(url, headers=headers)

    media_data_list = response.json()

    return media_data_list


def write_media_objects_to_db(media_objects):
    """Add the media_objects to the database if they don't exist, otherwise ignore them

    Arguments:
        media_objects {List} -- objects containing the vrt_media_id
    """
    for media_object in media_objects:
        obj = (
            db_session.query(MediaObject)
            .filter(MediaObject.vrt_media_id == media_object.vrt_media_id)
            .one_or_none()
        )
        if obj is None:
            db_session.add(media_object)
            log.info(
                "vrt media id written to DB", vrt_media_id=media_object.vrt_media_id
            )
    db_session.commit()


def process_media_ids():
    """requests metadata update for all media ids with status == 0"""
    objects = db_session.query(MediaObject).filter(MediaObject.status == 0).all()
    for obj in objects:
        success = request_metadata_update(obj.vrt_media_id.strip())
        obj.last_update = datetime.now()
        if success:
            obj.status = 1
            db_session.commit()
        else:
            obj.status = 2
            db_session.commit()
        time.sleep(1)


def request_metadata_update(media_id):
    """sends a request to update the metadata to the configured host. 

    Arguments:
        media_id {str} -- the VRT Media ID to be updated

    Returns:
        bool -- True if the call was succesful, False if failed
    """
    payload = {
        "media_id": media_id,
        "media_type": "metadata",
        "destination": "mediahaven",
    }

    log.info(
        "creating vrt metadata update request", vrt_media_id=media_id, request=payload
    )

    response = requests.post(
        cfg["environment"]["vrt_request_api"]["host"], data=json.dumps(payload)
    )

    if response.status_code == 200 and response.json()["status"] == "OK":
        log.info(
            "vrt metadata update request successful",
            vrt_media_id=media_id,
            status_code=response.status_code,
        )
        return True
    else:
        log.critical(
            "vrt metadata update request failed",
            vrt_media_id=media_id,
            status_code=response.status_code,
        )
        return False


def get_progress():
    """0 = in db, 1 = successful update req, 2 = update req failed

    Returns:
        Dict -- for each status show the number of items
    """
    amount_in_status_0 = (
        db_session.query(MediaObject).filter(MediaObject.status == 0).count()
    )
    amount_in_status_1 = (
        db_session.query(MediaObject).filter(MediaObject.status == 1).count()
    )
    amount_in_status_2 = (
        db_session.query(MediaObject).filter(MediaObject.status == 2).count()
    )
    progress = {
        "0": amount_in_status_0,
        "1": amount_in_status_1,
        "2": amount_in_status_2,
    }

    return json.dumps(progress)


def start():
    # mediahaven call so we can get total number of results
    media_data = get_fragments()

    number_of_media_ids = 0
    total_number_of_results = media_data["TotalNrOfResults"]

    if db_session.query(MediaObject).count() == total_number_of_results:
        # should skip to step 2
        number_of_media_ids = total_number_of_results

    # step 1: keep calling the mediahaven-api until all results are received
    while (
        number_of_media_ids < total_number_of_results
        and number_of_media_ids < cfg["max_amount_to_process"]
    ):
        # map items to a mediaobject
        media_objects = list(
            map(
                lambda x: MediaObject(x["Dynamic"]["dc_identifier_cpid"]),
                media_data["MediaDataList"],
            )
        )

        write_media_objects_to_db(media_objects)
        # update amount of items processed
        number_of_media_ids += len(media_objects)
        # get new fragments
        media_data = get_fragments(offset=number_of_media_ids)

    # step 2: send each media-id for update
    process_media_ids()


if __name__ == "__main__":
    start()
