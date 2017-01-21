"""
COPYRIGHT 2016 ESRI

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
__author__='joelwhitney'
"""
  Requires Python 3+
  A simple wrapper around the ArcREST API to make my life easier.... maybe.

  The AGOLHandler.py helper class provides a means to connect to AGOL/Portal
  and manage tokens.
"""

class Portal(object):
    """
    Wrapper around a Portal.
    http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r3000001m7000000
    """
    def __init__(self, jsonResponse):
        self._id = jsonResponse['id']

    @property
    def id(self):
        return self._id