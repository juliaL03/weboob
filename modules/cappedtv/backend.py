# -*- coding: utf-8 -*-

# Copyright(C) 2012 Lord
#
# This module is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

from __future__ import with_statement

from weboob.capabilities.video import ICapVideo
from weboob.tools.backend import BaseBackend
from .browser import CappedBrowser, CappedVideo


__all__ = ['CappedBackend']


class CappedBackend(BaseBackend, ICapVideo):
    NAME = 'cappedtv'
    MAINTAINER = 'Lord'
    EMAIL = 'lord@lordtoniok.com'
    VERSION = '0.c'
    DESCRIPTION = 'Capped.tv demoscene website'
    LICENSE = 'WTFPLv2'
    BROWSER = CappedBrowser

    def get_video(self, _id):
        with self.browser:
            return self.browser.get_video(_id)

    def search_videos(self, pattern=None, sortby=ICapVideo.SEARCH_RELEVANCE, nsfw=None, max_results=None):
        with self.browser:
            return self.browser.search_videos(pattern)

    def fill_video(self, video, fields):
        if fields != ['thumbnail']:
            with self.browser:
                video = self.browser.get_video(CappedVideo.id2url(video.id), video)
        if 'thumbnail' in fields and video.thumbnail:
            with self.browser:
                video.thumbnail.data = self.browser.readurl(video.thumbnail.url)

        return video

    OBJECTS = {CappedVideo: fill_video}
