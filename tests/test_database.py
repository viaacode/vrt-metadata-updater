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
from unittest.mock import patch
import json

from requests.exceptions import Timeout

import vrt_metadata_updater
from models import MediaObject

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

amount_in_progress = 42

class mockFilter(object):
    def __init__(self):
        self._count = amount_in_progress

    def count(self):
        return self._count

class mockQuery(object):
    def __init__(self, arg):
        self._filter = mockFilter()

    def filter(self, placeHolder):
        return self._filter

class TestMetadataUpdater(unittest.TestCase):
    def test_metadata_update_request(self):
        with patch("vrt_metadata_updater.db_session") as session:
            session.query.side_effect = mockQuery
            progress = vrt_metadata_updater.get_progress()
            assert progress == json.dumps({"0": amount_in_progress, "1": amount_in_progress, "2": amount_in_progress})


if __name__ == "__main__":
    unittest.main()
