import functools
import time

import requests
from requests.auth import HTTPBasicAuth
from viaa.configuration import ConfigParser
from viaa.observability import logging
from requests.exceptions import RequestException

logger = logging.get_logger(config=ConfigParser())


class AuthenticationException(Exception):
    """Exception raised when authentication fails."""
    pass


class MediahavenClient:
    def __init__(self, config: dict = None):
        self.cfg: dict = config
        self.token_info = None


    def __authenticate(function):
        @functools.wraps(function)
        def wrapper_authenticate(self, *args, **kwargs):
            if not self.token_info:
                self.token_info = self.__get_token()
            try:
                return function(self, *args, **kwargs)
            except AuthenticationException as error:
                self.token_info = self.__get_token()
            return function(self, *args, **kwargs)

        return wrapper_authenticate


    def __get_token(self) -> str:
        """Gets an OAuth token that can be used in mediahaven requests to authenticate."""
        user: str = self.cfg["environment"]["mediahaven"]["username"]
        password:str = self.cfg["environment"]["mediahaven"]["password"]
        url: str = self.cfg["environment"]["mediahaven"]["host"] + "/oauth/access_token"
        payload = {"grant_type": "password"}

        try:
            r = requests.post(
                url,
                auth=HTTPBasicAuth(user.encode("utf-8"), password.encode("utf-8")),
                data=payload,
            )

            if r.status_code != 201:
                raise ConnectionError(f"Failed to get a token. Status: {r.status_code}")
            token_info =  r.json()
        except ConnectionError as e:
            logger.critical(str(e))
            raise
        return token_info


    @__authenticate
    def get_fragments(self, offset: int = 0) -> dict:
        """Gets the next 1000 fragments at a time for a configured media type.

        Keyword Arguments:
            offset {int} -- offset for paging (default: {0})

        Returns:
            dict -- contains the fragments and the total number of results
        """
        url: str = (
            self.cfg["environment"]["mediahaven"]["host"] + "/media/"
        )

        headers: dict = {
            "Authorization": f"Bearer {self.token_info['access_token']}",
            "Accept": "application/vnd.mediahaven.v2+json"
            }

        params: dict = {
            "q": f'%2b(type_viaa:"{self.cfg["media_type"]}")',
            "startIndex": offset,
            "nrOfResults": self.cfg["nr_of_results"],
            }
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                )
        except RequestException as e:
            logger.critical(str(e))

        if response.status_code == 401:
            # AuthenticationException triggers a retry with a new token
            raise AuthenticationException(response.text)

        return response.json()
