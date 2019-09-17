#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  models.py
#   

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class MediaObject(Base):
    __tablename__ = "media_objects"

    vrt_media_id = Column(String, primary_key=True)
    status = Column(Integer)
    last_update = Column(DateTime)

    def __init__(self, vrt_media_id: str) -> None:
        self.vrt_media_id = vrt_media_id
        self.status = 0
        self.last_update = datetime.now()
