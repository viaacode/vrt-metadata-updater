#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  models.py
#   

from database import Base
from sqlalchemy import Column, DateTime, Integer, String
from datetime import datetime


class MediaObject(Base):
    __tablename__ = "media_objects"

    vrt_media_id = Column(String, primary_key=True)
    status = Column(Integer)
    last_update = Column(DateTime)

    def __init__(self, vrt_media_id):
        self.vrt_media_id = vrt_media_id
        self.status = 0
        self.last_update = datetime.now()
