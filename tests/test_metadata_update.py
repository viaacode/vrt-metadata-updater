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


if __name__ == "__main__":
    unittest.main()
