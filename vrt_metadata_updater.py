"""
Created on: 2019-08-22 10:47:21  

@Author: Rudolf De Geijter
"""

import functools
import logging
import pprint
import sys
import time

import requests
import structlog
import yaml
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

# CONSTANTS
nr_of_results = 10

# logger configuration
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    stream=sys.stdout
)

structlog.configure(
    processors=[structlog.stdlib.filter_by_level,  # First step, filter by level to
                structlog.stdlib.add_logger_name,  # module name
                structlog.stdlib.add_log_level,  # log level
                structlog.stdlib.PositionalArgumentsFormatter(),  # % formatting
                structlog.processors.StackInfoRenderer(),  # adds stack if stack_info=True
                structlog.processors.format_exc_info,  # Formats exc_info
                structlog.processors.UnicodeDecoder(),  # Decodes all bytes in dict to unicode
                structlog.processors.TimeStamper(fmt="iso"),  # Because timestamps! UTC by default
                structlog.stdlib.render_to_log_kwargs,  # Preps for logging call
                structlog.processors.JSONRenderer() # to json
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()

# Load config file
DEFAULT_CFG_FILE = './config.yml'
with open(DEFAULT_CFG_FILE, 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

token = ''


def authenticate(func):
    """Gets new token if no token"""
    @functools.wraps(func)
    def wrapper_authenticate(*args, **kwargs):
        global token
        if not token:
            token = get_token()
        return func(*args, **kwargs)
    return wrapper_authenticate


def slow_down(func):
    """Sleep 1 second before calling the function"""
    @functools.wraps(func)
    def wrapper_slow_down(*args, **kwargs):
        time.sleep(1)
        return func(*args, **kwargs)
    return wrapper_slow_down

def get_token():
    user = cfg['environment']['mediahaven']['username']
    password = cfg['environment']['mediahaven']['password']
    url = cfg['environment']['mediahaven']['host'] + '/oauth/access_token'
    payload = {'grant_type': 'password'}
    
    r = requests.post(url, 
                      auth=HTTPBasicAuth(user.encode('utf-8'), password.encode('utf-8')), 
                      data=payload)

    try:
        rtoken = r.json()['access_token']
        token = 'Bearer ' + rtoken    
    except Exception as e:
        out={'ERROR':str(e),
                'status code':r.status_code,
                'request body':str(r.text)}
        return None
    return token


@authenticate
def get_fragments(offset=0):
    url = cfg['environment']['mediahaven']['host'] + f'/media/?q=%2b(type_viaa:"{cfg["media_type"]}")&startIndex={offset}&nrOfResults={nr_of_results}'
    headers = {
        'Authorization': token,
        'Accept': "application/vnd.mediahaven.v2+json",
    }

    response = requests.request("GET", url=url, headers=headers)

    media_data_list = response.json()

    return media_data_list


@slow_down
def request_metadata_update(media_id):
    """sends a request to update the metadata to the configured host. No more than 1 request/second
    
    Arguments:
        media_id {str} -- the VRT Media ID to be updated
    """

    log.info("processing", media_id=media_id)

    payload = {"media_id": media_id,
               "media_type": "metadata",
               "destination": "mediahaven"}

    response = requests.post(cfg['environment']['vrt_request_api']['host'], data=payload)

    if response.status_code == 200:
        log.info("processed", media_id=media_id, status_code=response.status_code)
    else:
        log.error("error", media_id=media_id, status_code=response.status_code )
        # TODO: handle failure of the request
        pass

def main():
    media_data = get_fragments()

    number_of_media_ids = 0
    total_number_of_results = media_data['TotalNrOfResults']

    while number_of_media_ids < total_number_of_results:
        media_ids = list(map(lambda x: x['Dynamic']['dc_identifier_cpid'], media_data['MediaDataList']))
        with open(cfg['media_id_list'], 'a+') as f:
            for media_id in media_ids:
                f.write(f"{media_id}\n")
        number_of_media_ids += len(media_ids)
        media_data = get_fragments(offset=number_of_media_ids)
    
    # open file containing ids to be processed
    with open(cfg['media_id_list']) as f:
        #read each line until no more lines left
        for media_id in f:
            request_metadata_update(media_id.strip())
    



if __name__ == "__main__":
    main()
