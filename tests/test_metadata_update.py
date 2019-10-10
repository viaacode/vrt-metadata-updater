#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  tests/test_metadata_update.py
#

import os
import sys
import time
import unittest
from collections import namedtuple
from unittest.mock import patch

from requests.exceptions import Timeout, ConnectionError

from vrt_metadata_updater import VrtMetadataUpdater

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# class TestMetadataUpdater(unittest.TestCase):
#     def test_metadata_update_request(self):
#         # Arrange
#         mock_config = {
#             "environment": {
#                 "vrt_request_api": {
#                     "host": "http://0.0.0.0"
#                 },
#                 "mediahaven": {
#                     "host": "http://0.0.0.0",
#                     "username": "testuser",
#                     "password": "testpass"
#                 }
#             },
#             "media_type": "mock_type",
#             "max_amount_to_process": 0,
#             "nr_of_results": 1000,
#         }
#         def post(url, data) -> tuple:
#             Response = namedtuple("Response", ["status_code", "json"])
#             def json():
#                 return {"status": "OK"}
#             r = Response(200, json)
#             return r
#         with patch("vrt_metadata_updater.session") as mock_requests:
#             mock_requests.post.side_effect = post

#             # Act
#             vrt_metadata_updater = VrtMetadataUpdater(mock_config)
#             result = vrt_metadata_updater.request_metadata_update("1234")

#             # Assert
#             assert result == True
#             mock_requests.post.assert_called_once()


#     def test_metadata_update_request_fail(self):
#         # Arrange
#         mock_config = {
#             "environment": {
#                 "vrt_request_api": {
#                     "host": "http://0.0.0.0"
#                 },
#                 "mediahaven": {
#                     "host": "http://0.0.0.0",
#                     "username": "testuser",
#                     "password": "testpass"
#                 }
#             },
#             "media_type": "mock_type",
#             "max_amount_to_process": 0,
#             "nr_of_results": 1000,
#         }
#         def post(url, data) -> tuple:
#             Response = namedtuple("Response", ["status_code", "json"])
#             def json():
#                 return {"status": "NOK"}
#             r = Response(500, json)
#             return r
#         with patch("vrt_metadata_updater.requests") as mock_requests:
#             mock_requests.post.side_effect = post

#             # Act
#             vrt_metadata_updater = VrtMetadataUpdater(mock_config)
#             result = vrt_metadata_updater.request_metadata_update("1234")

#             # Assert
#             assert result == False
#             mock_requests.post.assert_called_once()


    # def test_get_fragments(self):
    #     # Arrange
    #     mock_config = {
    #         "environment": {
    #             "vrt_request_api": {
    #                 "host": "http://0.0.0.0"
    #             },
    #             "mediahaven": {
    #                 "host": "http://0.0.0.0",
    #                 "username": "testuser",
    #                 "password": "testpass"
    #             }
    #         },
    #         "media_type": "mock_type",
    #         "max_amount_to_process": 0,
    #         "nr_of_results": 1000,
    #     }
    #     def get(url, headers, params) -> tuple:
    #         Response = namedtuple("Response", ["status_code", "json"])
    #         def json():
    #             return {"status": "OK"}
    #         r = Response(200, json)
    #         return r
    #     with patch("vrt_metadata_updater.requests") as mock_requests:
    #         mock_requests.get.side_effect = get
    #             # Act
    #         vrt_metadata_updater = VrtMetadataUpdater(mock_config)
    #         with patch.object(vrt_metadata_updater, "_VrtMetadataUpdater__is_token_valid", return_value = True) as mock_token:
    #             vrt_metadata_updater.token_info = {"access_token": "token"}
    #             vrt_metadata_updater.get_fragments()

    #         # Assert
    #         mock_requests.get.assert_called_once()


    # def test_get_token_bad_config(self):
    #     # Arrange
    #     mock_config = {
    #         "environment": {
    #             "vrt_request_api": {
    #                 "host": "http://0.0.0.0"
    #             },
    #             "mediahaven": {
    #                 "host": "http://0.0.0.0",
    #                 "username": "testuser",
    #                 "password": "testpass"
    #             }
    #         },
    #         "media_type": "mock_type",
    #         "max_amount_to_process": 0,
    #         "nr_of_results": 1000,
    #     }
    #     # Act
    #     with self.assertRaises(ConnectionError):
    #         vrt_metadata_updater = VrtMetadataUpdater(mock_config)
    #         result = vrt_metadata_updater._VrtMetadataUpdater__get_token()

    # def test_get_token_mediahaven_fail(self):
    #     # Arrange
    #     mock_config = {
    #         "environment": {
    #             "vrt_request_api": {
    #                 "host": "http://0.0.0.0"
    #             },
    #             "mediahaven": {
    #                 "host": "http://0.0.0.0",
    #                 "username": "testuser",
    #                 "password": "testpass"
    #             }
    #         },
    #         "media_type": "mock_type",
    #         "max_amount_to_process": 0,
    #         "nr_of_results": 1000,
    #     }
    #     def post(url, auth, data) -> tuple:
    #         Response = namedtuple('Response', ['status_code'])
    #         r = Response(500)
    #         return r
    #     # Act
    #     with patch("vrt_metadata_updater.requests") as mock_requests:
    #         mock_requests.post.side_effect = post
    #         with self.assertRaises(ConnectionError):
    #             vrt_metadata_updater = VrtMetadataUpdater(mock_config)
    #             result = vrt_metadata_updater._VrtMetadataUpdater__get_token()


    # def test_get_token_mediahaven_success(self):
    #     # Arrange
    #     mock_config = {
    #         "environment": {
    #             "vrt_request_api": {
    #                 "host": "http://0.0.0.0"
    #             },
    #             "mediahaven": {
    #                 "host": "http://0.0.0.0",
    #                 "username": "testuser",
    #                 "password": "testpass"
    #             }
    #         },
    #         "media_type": "mock_type",
    #         "max_amount_to_process": 0,
    #         "nr_of_results": 1000,
    #     }
    #     def post(url, auth, data) -> tuple:
    #         Response = namedtuple("Response", ["status_code", "json"])
    #         def json():
    #             return {
    #                 "token_type": "Bearer",
    #                 "expires_in": 1800,
    #                 "access_token": "1234567890qwertyuiop",
    #             }
    #         r = Response(201, json)
    #         return r
    #     # Act
    #     with patch("vrt_metadata_updater.requests") as mock_requests:
    #         mock_requests.post.side_effect = post
    #         vrt_metadata_updater = VrtMetadataUpdater(mock_config)
    #         result = vrt_metadata_updater._VrtMetadataUpdater__get_token()
    #         result["expires_at"] = int(time.time()) + result["expires_in"]
    #         is_token_valid = vrt_metadata_updater._VrtMetadataUpdater__is_token_valid(result)

    #     # Assert
    #     assert is_token_valid == True
    #     assert result["access_token"] == "1234567890qwertyuiop"


if __name__ == "__main__":
    unittest.main()
