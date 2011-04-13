# -*- coding: utf-8 -*-

# Copyright(C) 2011 Laurent Bachelier
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


from weboob.tools.browser import BaseBrowser

from .pages import PastePage

__all__ = ['PastealaconBrowser']

class PastealaconBrowser(BaseBrowser):
    DOMAIN = 'pastealacon.com'
    ENCODING = 'ISO-8859-1'
    PAGES = {'http://%s/(?P<id>\d+)' % DOMAIN: PastePage}

    def fill_paste(self, paste):
        """
        Get as much as information possible from the paste page
        """
        self.location(paste.page_url)
        return self.page.fill_paste(paste)

    def get_contents(self, _id):
        """
        Get the contents from the raw URL
        This is the fastest and safest method if you only want the content.
        Returns unicode.
        """
        return self.readurl('http://%s/pastebin.php?dl=%s' % (self.DOMAIN, _id)).decode(self.ENCODING)
