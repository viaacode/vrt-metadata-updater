#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  vrt_metadata_updater.py
#  

import functools
import json
import logging
import sys
import time
from datetime import datetime

import requests
import structlog
import yaml
from requests.auth import HTTPBasicAuth

from database import db_session, init_db
from models import MediaObject
from viaa.logging import get_logger

# Load config file
DEFAULT_CFG_FILE = "./config.yml"
with open(DEFAULT_CFG_FILE, "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

token = ""

logger = get_logger()

def authenticate(func):
    """Gets a new token if no token is present."""

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
        logger.critical(str(e))
        return None
    return token


@authenticate
def get_fragments(offset=0):
    """Gets the next 100 fragments at a time for a configured media type.

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
    """Add the media_objects to the database if they don't exist, otherwise ignore them.

    Arguments:
        media_objects {List} -- objects containing the vrt_media_id
    """
    for media_object in media_objects:
        obj = (
            db_session.query(MediaObject)
            .filter(MediaObject.vrt_media_id == media_object.vrt_media_id)
            .first()
        )
        if obj is None:
            db_session.add(media_object)
            logger.info(
                "vrt media id written to DB", vrt_media_id=media_object.vrt_media_id
            )
            db_session.commit()


def process_media_ids():
    """Requests a metadata update for all media ids with status equal to zero."""
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
    """Sends a request to update the metadata to the configured host. 

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

    logger.info(
        "creating vrt metadata update request", vrt_media_id=media_id, request=payload
    )

    response = requests.post(
        cfg["environment"]["vrt_request_api"]["host"], data=json.dumps(payload)
    )

    if response.status_code == 200 and response.json()["status"] == "OK":
        logger.info(
            "vrt metadata update request successful",
            vrt_media_id=media_id,
            status_code=response.status_code,
        )
        return True
    else:
        logger.critical(
            "vrt metadata update request failed",
            vrt_media_id=media_id,
            status_code=response.status_code,
        )
        return False


def get_progress():
    """Returns the current status of the script as a dictionary.
    status 0 = in db
    status 1 = successful update req
    status 2 = update req failed

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
    while number_of_media_ids < total_number_of_results and (
        number_of_media_ids < cfg["max_amount_to_process"]
        or cfg["max_amount_to_process"] == 0
    ):
        media_objects = list()
        # map items to a mediaobject if they have a dc_identifier_localid
        for item in media_data["MediaDataList"]:
            if "dc_identifier_localid" in item["Dynamic"]:
                media_objects.append(
                    MediaObject(item["Dynamic"]["dc_identifier_localid"])
                )

        write_media_objects_to_db(media_objects)
        # update amount of items processed
        number_of_media_ids += len(media_objects)
        # get new fragments
        media_data = get_fragments(offset=number_of_media_ids)

    # step 2: send each media-id for update
    process_media_ids()


if __name__ == "__main__":
    logger.info("starting")
    init_db()
    start()
