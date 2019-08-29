"""
Created on: 2019-08-22 10:47:21

@Author: Rudolf De Geijter
"""

import functools
import json
import logging
import sys
import time

import requests
import structlog
import yaml
from requests.auth import HTTPBasicAuth

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

    r = requests.post(
        url,
        auth=HTTPBasicAuth(user.encode("utf-8"), password.encode("utf-8")),
        data=payload,
    )

    try:
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


def write_media_ids_to_file(media_ids):
    """appends each media id as a new line to the configured file

    Arguments:
        media_ids {List[str]} -- list of media ids to be added
    """
    with open(cfg["media_id_list"], "a+") as f:
        for media_id in media_ids:
            f.write(f"{media_id}\n")
            log.info(
                "vrt media id written to file",
                vrt_media_id=media_id,
                file_name=cfg["media_id_list"],
            )


def request_metadata_update(media_id):
    """sends a request to update the metadata to the configured host. 

    Arguments:
        media_id {str} -- the VRT Media ID to be updated
    """
    payload = {
        "media_id": media_id,
        "media_type": "metadata",
        "destination": "mediahaven",
    }

    log.info(
        "creating vrt metadata update request",
        vrt_media_id=media_id,
        request=payload,
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
    else:
        log.critical(
            "vrt metadata update request failed",
            vrt_media_id=media_id,
            status_code=response.status_code,
        )


def main():
    # mediahaven call so we can get total number of results
    media_data = get_fragments()

    number_of_media_ids = 0
    total_number_of_results = media_data["TotalNrOfResults"]

    # keep calling the mediahaven-api until all results are received
    while number_of_media_ids < total_number_of_results:
        # map items to their vrt media id
        media_ids = list(
            map(
                lambda x: x["Dynamic"]["dc_identifier_cpid"],
                media_data["MediaDataList"],
            )
        )
        write_media_ids_to_file(media_ids)
        number_of_media_ids += len(media_ids)
        media_data = get_fragments(offset=number_of_media_ids)

    # open file containing ids to be processed
    with open(cfg["media_id_list"]) as f:
        for media_id in f:
            request_metadata_update(media_id.strip())
            time.sleep(1)


if __name__ == "__main__":
    main()
