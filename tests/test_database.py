#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  tests/test_metadata_update.py
#  

import json
import os
import sys
import unittest
from unittest.mock import patch

from requests.exceptions import Timeout

from models import MediaObject
from vrt_metadata_updater import VrtMetadataUpdater

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

amount_in_progress = 42

class MockFilter(object):
    def __init__(self):
        self._count = amount_in_progress


    def count(self):
        return self._count
    
    
    def first(self):
        return None
    
    
    def all(self):
        return [MediaObject('test1'), MediaObject('test2')]

class MockQuery(object):
    def __init__(self, arg):
        self._filter = MockFilter()


    def filter(self, placeHolder):
        return self._filter


class TestMetadataUpdater(unittest.TestCase):
    def test_metadata_update_request(self):
        # Arrange
        with patch("vrt_metadata_updater.db_session") as session:
            session.query.side_effect = MockQuery
            vrt_metadata_updater = VrtMetadataUpdater({})
            
            # Act
            progress = vrt_metadata_updater.get_progress()
            
            # Assert
            assert progress == json.dumps({"0": amount_in_progress, "1": amount_in_progress, "2": amount_in_progress})
            
    
    def test_write_media_objects(self):
        # Arrange
        media_objects = [MediaObject('test1'), MediaObject('test2')]
        
        # Act
        vrt_metadata_updater = VrtMetadataUpdater({})
        vrt_metadata_updater.write_media_objects_to_db(media_objects)
        with patch("vrt_metadata_updater.db_session") as session:
            session.query.side_effect = MockQuery
            vrt_metadata_updater = VrtMetadataUpdater({})
            vrt_metadata_updater.write_media_objects_to_db(media_objects)
            
        # Assert
        assert session.add.call_count == 2
        assert session.commit.call_count == 2
        
    
    def test_process_media_ids(self):
        # Arrange
        media_objects = [MediaObject('test1'), MediaObject('test2')]

        # Act
        with patch("vrt_metadata_updater.VrtMetadataUpdater.request_metadata_update") as mock_request_update:
            mock_request_update.return_value = True
            vrt_metadata_updater = VrtMetadataUpdater({})
            vrt_metadata_updater.process_media_objects(media_objects)
            
        # Assert
        assert media_objects[0].status == 1
        assert media_objects[1].status == 1
        
        
    def test_process_media_ids_request_failed(self):
        # Arrange
        media_objects = [MediaObject('test1'), MediaObject('test2')]

        assert media_objects[0].status == 0

        # Act
        with patch("vrt_metadata_updater.VrtMetadataUpdater.request_metadata_update") as mock_request_update:
            mock_request_update.return_value = False
            vrt_metadata_updater = VrtMetadataUpdater({})
            vrt_metadata_updater.process_media_objects(media_objects)
            
        # Assert
        assert mock_request_update.call_count == 2
        assert media_objects[0].status == 2
        assert media_objects[1].status == 2    
        
           
if __name__ == "__main__":
    unittest.main()
