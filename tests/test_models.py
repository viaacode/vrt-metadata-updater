#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  tests/test_models.py
#

import os
import sys
import time
import unittest
from datetime import datetime

import pytest

from models import MediaObject

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestModels(unittest.TestCase):
    def test_new_mediaobject(self):
        test_mediaobject = MediaObject('123test')
        assert test_mediaobject.vrt_media_id == '123test'
        assert test_mediaobject.status == 0


    def test_new_mediaobject_no_id(self):
        with self.assertRaises(TypeError):
            test_mediaobject = MediaObject()


if __name__ == "__main__":
    unittest.main()
