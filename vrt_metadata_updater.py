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
from typing import Dict, List

import requests
import structlog
import yaml
from requests.exceptions import RequestException
from requests.packages.urllib3.util import Retry
from requests.adapters import HTTPAdapter
from requests import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import insert
from viaa.configuration import ConfigParser
from viaa.observability import logging

from database import db_session, init_db
from models import MediaObject
from mediahaven import MediahavenClient

logger = logging.get_logger(config=ConfigParser())

class VrtMetadataUpdater():
    def __init__(self, config: dict):
        self.cfg: dict = config
        self.token_info = None


    def write_media_objects_to_db(self, media_objects: List[MediaObject]) -> None:
        """Add the media_objects to the database if they don't exist, otherwise ignore them.

        Arguments:
            media_objects {List} -- objects containing the vrt_media_id
        """
        media_objects_as_dict = [media_object.get_dict() for media_object in media_objects]
        try:
            db_session.execute(MediaObject.__table__.insert(prefixes=['OR IGNORE']), media_objects_as_dict)
            db_session.commit()
        except SQLAlchemyError as exception:
            db_session.rollback()
            logger.warning("Something went wrong when trying to write media id's to the database.")


    def process_media_objects(self, list_of_media_objects: List[MediaObject]) -> None:
        """Requests a metadata update and updates the status for all media objects."""
        for obj in list_of_media_objects:
            success = self.request_metadata_update(obj.vrt_media_id.strip())
            obj.last_update = datetime.now()
            if success:
                obj.status = 1
            else:
                obj.status = 2
            try:
                db_session.commit()
                end = int(time.time())
            except SQLAlchemyError as exception:
                db_session.rollback()
                logger.warning(f"Failed to update the status of {obj.vrt_media_id}.")
            time.sleep(self.cfg["throttle_time"])


    def request_metadata_update(self, media_id: str) -> bool:
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

        retries = Retry(total=10, backoff_factor=0.5, status_forcelist=[ 500, 502, 503, 504, 521], method_whitelist=frozenset(['GET', 'POST']))
        s = Session()
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))

        try:
            response = s.post(
                self.cfg["environment"]["vrt_request_api"]["host"], data=json.dumps(payload)
            )
        except RequestException as exception:
            logger.warning(f"Something went wrong trying update metadata: {str(exception)}")

        if response.status_code == 200 and response.json()["status"] == "OK":
            logger.info(
                "vrt metadata update request successful",
                vrt_media_id=media_id,
                status_code=response.status_code,
            )
            return True
        else:
            return False


    def get_progress(self) -> str:
        """Returns the current status of the script as a JSON string.
        items_in_db = all items in db
        no_update_request = media id from mediahaven is in the database but no updaterequest has been done
        update_requests_succes = a metadata update has been requested and api returned success
        update_requests_failed = a metadata update has been requested but api returned failed

        Returns:
            str -- for each status show the number of items
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
            "items_in_db": amount_in_status_0 + amount_in_status_1 + amount_in_status_2,
            "no_update_request": amount_in_status_0,
            "update_requests_succes": amount_in_status_1,
            "update_requests_failed": amount_in_status_2,
        }

        return json.dumps(progress)


    def start(self) -> None:
        logger.debug("Starting VRT metadata updater...")

        mediahaven_client = MediahavenClient(self.cfg)

        # mediahaven call so we can get total number of results
        media_data = mediahaven_client.get_fragments()

        number_of_media_ids = 0
        total_number_of_results = media_data["TotalNrOfResults"]
        total_number_of_items_in_db = db_session.query(MediaObject).count()

        logger.debug(f"{total_number_of_results} items found in MediaHaven.")
        # If all media ids are already in the database, we skip to step 2
        if total_number_of_items_in_db == total_number_of_results or self.cfg["skip_mediahaven"]:
            logger.debug("All ids already in database, skipping to step 2.")
            # should skip to step 2
            number_of_media_ids = total_number_of_results

        # step 1: keep calling the mediahaven-api until all results are received
        while number_of_media_ids < total_number_of_results and (
            number_of_media_ids < self.cfg["max_amount_to_process"]
            or self.cfg["max_amount_to_process"] == 0
        ):
            media_objects = list()
            # map items to a mediaobject if they have a dc_identifier_localid
            for item in media_data["MediaDataList"]:
                if "dc_identifier_localid" in item["Dynamic"]:
                    media_objects.append(
                        MediaObject(item["Dynamic"]["dc_identifier_localid"])
                    )
                else:
                    # Reduce total_number_of_results by one to prevent endless loop
                    logger.debug(f'Item without localid found: {json.dumps(item)}')
                    total_number_of_results = total_number_of_results - 1

            self.write_media_objects_to_db(media_objects)
            # update amount of items processed
            number_of_media_ids += len(media_objects)
            # get new fragments
            media_data = mediahaven_client.get_fragments(offset=number_of_media_ids)

        # step 2: send each media object with status 0 for update
        objects: List[MediaObject] = db_session.query(MediaObject).filter(MediaObject.status != 1).all()

        self.process_media_obwrapcjects(objects)


if __name__ == "__main__":
    # Always initialize databse to be sure it exists with the correct tables.
    init_db()

    DEFAULT_CFG_FILE = "./config.yml"
    # Load config file
    with open(DEFAULT_CFG_FILE, "r") as ymlfile:
        cfg: dict = yaml.load(ymlfile, Loader=yaml.FullLoader)

    VrtMetadataUpdater(cfg).start()
