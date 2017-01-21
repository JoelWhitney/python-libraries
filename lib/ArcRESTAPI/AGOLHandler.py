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
import urllib
import urllib.parse
import urllib.request
import json
from ArcRESTAPI.FeatureServices import *
from ArcRESTAPI.Portal import *

class AGOLHandler(object):
    """
    ArcGIS Online handler class:
      -Generates and keeps tokens
      -Allows search of content
      -Creates Feature Service
      -Copy existing Feature Services
      -Adds/Deletes features from Feature Service
    """

    def __init__(self, username, password, sourcePortal='https://www.arcgis.com'):
        self.username = username
        self.password = password
        self.sourcePortal = sourcePortal
        self.handler_token, self.http, self.expires = self.get_token()
        self._portal = self.get_portal_info()
        self._user_info = self.get_user_info()
        self._user_items = self.get_user_content()

    def get_token(self, exp=60):  # expires in 60 minutes
        parameters = urllib.parse.urlencode({'username': self.username,
                                             'password': self.password,
                                             'client': 'referer',
                                             'referer': self.sourcePortal,
                                             'expiration': exp,
                                             'f': 'json'}).encode("utf-8")
        request = self.sourcePortal + '/sharing/rest/generateToken?'
        json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
        try:
            if 'token' in json_response:
                return json_response['token'], request, json_response['expires']
            elif 'error' in json_response:
                print(json_response['error']['message'])
                for detail in json_response['error']['details']:
                    print(detail)
        except ValueError as e:
            print('An unspecified error occurred.')
            print(e)

    def get_info(self):
        '''Returns the description for a Portal for ArcGIS item.'''
        parameters = urllib.parse.urlencode({'token': self.token, 'f': 'json'}).encode("utf-8")
        request = self.sourcePortal + '/sharing/rest/content/items?'
        json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
        return json_response

    def get_portal_info(self):
        '''Returns the description for a Portal for ArcGIS item.'''
        parameters = urllib.parse.urlencode({'token': self.token, 'f': 'json'}).encode("utf-8")
        request = self.sourcePortal + '/sharing/rest/portals/self?'
        json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
        return Portal(json_response)

    def get_user_info(self):
        '''Returns the description for a Portal for ArcGIS item.'''
        parameters = urllib.parse.urlencode({'token': self.token, 'f': 'pjson'}).encode("utf-8")
        request = self.sourcePortal + '/sharing/rest/content/users/' + self.username + '?'
        json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
        return json_response

    def search(self, query=None, numResults=100, sortField='numviews', sortOrder='desc', start=0, token=None):
        '''Retrieve a single page of search results.'''
        parameters = {'q': query,
                      'num': numResults,
                      'sortField': sortField,
                      'sortOrder': sortOrder,
                      'f': 'json',
                      'start': start}
        if token:
            parameters['token'] = token
        parameters = urllib.parse.urlencode(parameters).encode("utf-8")
        request = self.sourcePortal + '/sharing/rest/search?'
        json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
        print(json_response)
        if len(json_response['results']) > 1:
            return AGOLItems(self, json_response['results']).results
        elif len(json_response['results']) == 1:
            return AGOLItem(self, json_response['results'][0])
        else:
            print("Appears to be no results..")

    def get_user_content(self):
        parameters = urllib.parse.urlencode({'token': self.token, 'f': 'json'}).encode("utf-8")
        request = self.sourcePortal + '/sharing/rest/content/users/' + self.username + '?'
        json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
        #return json_response
        return AGOLItems(self, json_response['items']).results

    def get_item_description(self, item_id):
        '''Returns the description for a Portal for ArcGIS item.'''
        parameters = urllib.parse.urlencode({'token': self.token, 'f': 'json'}).encode("utf-8")
        request = self.sourcePortal + '/sharing/rest/content/items/' + item_id + '?'
        json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
        return json_response

    def get_itemdata(self, item_id):
        '''Returns the description for a Portal for ArcGIS item.'''
        parameters = urllib.parse.urlencode({'token': self.token, 'f': 'json'}).encode("utf-8")
        request = self.sourcePortal + '/sharing/rest/content/items/' + item_id + '/data?'
        json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
        return json_response

    def delete_features(self, service_url, layer_id=0, where='ObjectId>0'):
        '''Returns the description for a Portal for ArcGIS item.
        http://resources.arcgis.com/en/help/arcgis-rest-api/#/Delete_Features/02r3000000w4000000/'''
        parameters = urllib.parse.urlencode({'where': where,
                                             'f': 'json',
                                             'token': self.token}).encode("utf-8")
        request = service_url + '/{}/deleteFeatures?'.format(str(layer_id))
        try:
            json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
            if 'deleteResults' in json_response:
                return json_response
            elif 'error' in json_response:
                print(json_response['error']['code'])
                print(json_response['error']['message'])
                for detail in json_response['error']['details']:
                    print(detail)
        except ValueError as e:
            print('An unspecified error occurred.')
            print(e)

    def add_features(self, service_url, agol_json, layer_id=0):
        '''Returns the description for a Portal for ArcGIS item.
        http://resources.arcgis.com/en/help/arcgis-rest-api/#/Add_Features/02r30000010m000000/'''
        parameters = urllib.parse.urlencode({'features': agol_json,
                                             'f': 'json',
                                             'token': self.token}).encode("utf-8")
        request = service_url + '/{}/addFeatures?'.format(str(layer_id))
        print(request)
        try:
            json_response = json.loads(urllib.request.urlopen(request, parameters).read().decode("utf-8"))
            if 'deleteResults' in json_response:
                return json_response
            elif 'error' in json_response:
                print(json_response['error']['code'])
                print(json_response['error']['message'])
                for detail in json_response['error']['details']:
                    print(detail)
        except ValueError as e:
            print('An unspecified error occurred.')
            print(e)

    def copy_feature_server(self, feature_server_url, feature_server_name):
        copied_feature_server = AGOLFeatureServer(feature_server_url, feature_server_name)
        print(copied_feature_server.layers)
        for layer in copied_feature_server.layers:
            print(layer.service_definition)
        new_feature_server = self.__create_feature_service(copied_feature_server.createParameters_template, feature_server_name)
        new_feature_server = new_feature_server.add_layers(copied_feature_server.layers)
        return new_feature_server

    def write_jsonfile(self, returned_json, filename='\json_file'):
        print(returned_json)
        with open(filename + '.json', 'w') as outfile:
            json.dump(returned_json, outfile, sort_keys=False, indent=4, ensure_ascii=False)

    def __create_feature_service(self, create_parameters, feature_server_name):
        user_content_url = self.sourcePortal + "/sharing/rest/content/users/" + self.username
        parameters = urllib.parse.urlencode({"createParameters": create_parameters,
                                             "outputType": "featureService",
                                             "f": "json",
                                             "token": self.token}).encode("utf-8")
        create_service_request = user_content_url + '/createService?'
        print(create_service_request)
        json_response = json.loads(urllib.request.urlopen(create_service_request, parameters).read().decode("utf-8"))
        print(json_response)
        if 'error' not in json_response:
            return AGOLFeatureServer(json_response['serviceurl'], feature_server_name, agol_handler=self)
        else:
            print(json_response)
            print('Code: {}'.format(json_response['error'].get('code', 'None')))
            print('Message: {}'.format(json_response['error'].get('message', 'None')))
            for detail in json_response['error'].get('details', []):
                print(detail)

    def __add_layer(self, layer):
        pass

    def __add_features(self, layer):
        pass

    @property
    def info(self):
        return self._info

    @property
    def portal(self):
        return self._portal

    @property
    def user_items(self):
        return self._user_items

    @property
    def token(self):
        return self.handler_token

class AGOLError(object):

    def __init__(self):
        pass


class AGOLItems(object):
    """
    Wrapper around the AGOLHandler search function.
    """
    def __init__(self, agol_handler, json_response):
        self._agol_handler = agol_handler
        self._response = json_response
        self._results = []
        for json_result in json_response:
            self._results.append(AGOLItem(agol_handler, json_result))

    def some_function(self):
        pass

    @property
    def raw_response(self):
        return self._response

    @property
    def results(self):
        return self._results


class AGOLItem(object):
    """
    Each result in AGOLSearchResults is of this type.
    """

    def __init__(self, agol_handler, json_result):
        self._agol_handler = agol_handler
        self._json_result = json_result
        self._type = json_result.get('type', None)
        self._owner = json_result.get('owner', None)
        self._id = json_result.get('id', None)
        self._title = json_result.get('title', None)
        self._name = json_result.get('name', None)
        self._description = json_result.get('description', None)
        self._access = json_result.get('access', None)
        self._typeKeywords = json_result.get('typeKeywords', None)
        self._tags = json_result.get('tags', None)
        self._url = json_result.get('url', None)
        self._spatialReference = json_result.get('spatialReference', None)

    @property
    def raw_result(self):
        return self._json_result

    @property
    def type(self):
        return self._type

    @property
    def owner(self):
        return self._owner

    @property
    def id(self):
        return self._id

    @property
    def title(self):
        return self._title

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def access(self):
        return self._access

    @property
    def typeKeywords(self):
        return self._typeKeywords

    @property
    def tags(self):
        return self._tags

    @property
    def url(self):
        return self._url
