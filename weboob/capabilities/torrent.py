# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012 Romain Bignon, Laurent Bachelier
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


from .base import Capability, BaseObject, Field, StringField, FloatField, \
                  IntField, UserError
from .date import DateField

__all__ = ['MagnetOnly', 'Torrent', 'CapTorrent']


class MagnetOnly(UserError):
    """
    Raised when trying to get URL to torrent but only magnet is available.
    """
    def __init__(self, magnet):
        self.magnet = magnet
        UserError.__init__(self, 'Only magnet URL is available')


class Torrent(BaseObject):
    """
    Torrent object.
    """
    name =      StringField('Name of torrent')
    size =      FloatField('Size of torrent')
    date =      DateField('Date when torrent has been published')
    url =       StringField('Direct url to .torrent file')
    magnet =    StringField('URI of magnet')
    seeders =   IntField('Number of seeders')
    leechers =  IntField('Number of leechers')
    files =     Field('Files in torrent', list)
    description =   StringField('Description of torrent')
    filename =      StringField('Name of .torrent file')

    def __init__(self, id, name):
        BaseObject.__init__(self, id)
        self.name = name


class CapTorrent(Capability):
    """
    Torrent trackers.
    """
    def iter_torrents(self, pattern):
        """
        Search torrents and iterate on results.

        :param pattern: pattern to search
        :type pattern: str
        :rtype: iter[:class:`Torrent`]
        """
        raise NotImplementedError()

    def get_torrent(self, _id):
        """
        Get a torrent object from an ID.

        :param _id: ID of torrent
        :type _id: str
        :rtype: :class:`Torrent`
        """
        raise NotImplementedError()

    def get_torrent_file(self, _id):
        """
        Get the content of the .torrent file.

        :param _id: ID of torrent
        :type _id: str
        :rtype: str
        """
        raise NotImplementedError()
