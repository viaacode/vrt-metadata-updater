#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  tests/test_metadata_update.py
#  

import os
import sys

import unittest
from requests.exceptions import Timeout
from unittest.mock import patch
import vrt_metadata_updater

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestMetadataUpdater(unittest.TestCase):
    def test_metadata_update_request(self):
        with patch("vrt_metadata_updater.requests") as mock_requests:
            mock_requests.post.side_effect = Timeout
            with self.assertRaises(Timeout):
                vrt_metadata_updater.request_metadata_update("1234")
                mock_requests.post.assert_called_once()

    def test_write_to_file(self):
        filename = "tests/test_list.txt"
        id_list = ["1", "2", "3"]

        if os.path.exists(filename):
            os.remove(filename)
        vrt_metadata_updater.cfg["media_id_list"] = filename
        vrt_metadata_updater.write_media_ids_to_file(id_list)
        test_list_content = []
        with open(filename) as f:
            for media_id in f:
                test_list_content.append(media_id.strip())

        self.assertEqual(test_list_content, id_list)


if __name__ == "__main__":
    unittest.main()
