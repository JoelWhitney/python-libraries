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
"""
import urllib
import urllib.parse
import urllib.request
import json

class AGOLHandler(object):
    """
    ArcGIS Online handler class.
      -Generates and keeps tokens
      -Allows search of content
      -Creates Feature Service
      -Adds/Deletes features from Feature Service
    """

    def __init__(self, username, password, sourcePortal='https://www.arcgis.com'):
        self.username = username
        self.password = password
        self.sourcePortal = sourcePortal
        self.handler_token, self.http, self.expires = self.get_token()
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
        self.__create_feature_service(copied_feature_server.createParameters_template)
        self.__add_layers(copied_feature_server)
        return copied_feature_server.url

    def __create_feature_service(self, create_parameters):
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
            return AGOLFeatureServer(json_response['serviceurl'], agol_handler=self)
        else:
            print(json_response)
            print('Code: {}'.format(json_response['error'].get('code', 'None')))
            print('Message: {}'.format(json_response['error'].get('message', 'None')))
            for detail in json_response['error'].get('details', []):
                print(detail)

    def __add_layers(self, copied_feature_server):
        # add service definition for each layer in one rest call
        layers = []
        for layer in copied_feature_server.layers:
            self.__add_layer(layer)
        # add features to the layers

    def __add_layer(self, layer):
        pass

    def __add_features(self, layer):
        pass

    @property
    def user_items(self):
        return self._user_items

    @property
    def token(self):
        return self.handler_token

class AGOLError(object):

    def __init__(self):
        pass


class AGOLFeatureServer(object):
    """
    Wrapper around the AGOLHandler create service function.
    """
    def __init__(self, feature_server_url, feature_server_name, agol_handler=None):
        self._feature_server_url = feature_server_url
        self._feature_server_name = feature_server_name
        self._agol_handler = agol_handler
        self._service_definition = self.__service_definition()
        self._create_parameters_template = self.__get_create_parameters()
        self._item_id = ''
        self._layers = []
        self.get_layers()

    def get_layers(self):
        layers = []
        for layer in self.service_definition['layers']:
            fs_layer_url = self._feature_server_url + '/{}'.format(layer['id'])
            layers.append(AGOLFeatureServerLayer(fs_layer_url, self._agol_handler))
        self._layers = layers

    def write_jsonfile(self, returned_json, filename='\json_file'):
        print(returned_json)
        with open(filename + '.json', 'w') as outfile:
            json.dump(returned_json, outfile, sort_keys=False, indent=4, ensure_ascii=False)

    def __service_definition(self):
        parameters = urllib.parse.urlencode({'f': 'pjson'}).encode("utf-8")
        request_url = self._feature_server_url
        response = urllib.request.urlopen(request_url, parameters).read().decode("utf-8")
        print(response)
        jsonResponse = json.loads(response)
        jsonResponse['name'] = self._feature_server_name
        return jsonResponse

    def __get_create_parameters(self):
        """only need specific portions of the entire service definition to create a 'copy'"""
        createParameterTemplate = {}
        createParameterOptions = ['name', 'serviceDescription', 'hasStaticData', 'maxRecordCount', 'supportedQueryFormats',
                                  'capabilities', 'description', 'copyrightText', 'spatialReference', 'initialExtent',
                                  'allowGeometryUpdates', 'units', 'xssPreventionInfo']
        for paramater in createParameterOptions:
            if paramater in self._service_definition:
                createParameterTemplate[paramater] = self._service_definition[paramater]
        return createParameterTemplate

    def add_layers(self):
        layers = []
        for layer in self._layers:
            layer = {"id": layer.id, "name": layer.name}

        """UPDATE DEFINITION WITH ABOVE???"""
        #url = 'http://services.arcgis.com/N4jtru9dctSQR53c/ArcGIS/rest/admin/services/Storm%20Discharge%20Points/FeatureServer/addToDefinition'
        url = 'http://services.arcgis.com/{}/ArcGIS/rest/admin/services/{}/FeatureServer/addToDefinition?'.format(self.id, name )
        parameters = urllib.parse.urlencode({'layers': [servicedefinition]}).encode("utf-8")
        # request_url = self._feature_service_url + '/addToDefinition?'
        jsonResponse = json.loads(urllib.request.urlopen(request_url, parameters).read().decode("utf-8"))
        print(jsonResponse)
        return jsonResponse

    @property
    def url(self):
        return self._feature_server_url

    @property
    def item_id(self):
        return self._item_id

    @property
    def service_definition(self):
        return self._service_definition

    @property
    def createParameters_template(self):
        return self._create_parameters_template

    @property
    def layers(self):
        return self._layers


class AGOLFeatureServerLayer(object):
    """
    Wrapper around the AGOLHandler create service function.
    """
    def __init__(self, feature_server_layer_url, agol_handler=None):
        self._agol_handler = agol_handler
        self._feature_server_layer_url = feature_server_layer_url
        self._service_definition = self.__service_definition()
        self._name = self._service_definition['name']
        self._layer_id = self._service_definition['id']
        self._type = self._service_definition['type']

    def write_jsonfile(self, returned_json, filename='\json_file'):
        print(returned_json)
        with open(filename + '.json', 'w') as outfile:
            json.dump(returned_json, outfile, sort_keys=False, indent=4, ensure_ascii=False)

    def add_features(self, agol_json):
        parameters = {'features': agol_json,
                      'f': 'json'}
        if self._agol_handler: parameters['token'] = self._agol_handler.token
        parameters = urllib.parse.urlencode(parameters).encode("utf-8")
        print(str(self._layer_id))
        request = self._feature_service_url + '/{}/addFeatures?'.format(self.layer_id)
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

    def delete_features(self, where='ObjectId>0'):
        parameters = {'where': where,
                      'f': 'pjson'}
        if self._agol_handler: parameters['token'] = self._agol_handler.token
        parameters = urllib.parse.urlencode(parameters).encode("utf-8")
        request = self._feature_service_url + '/{}/deleteFeatures?'.format(self.layer_id)
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

    def __service_definition(self):
        parameters = urllib.parse.urlencode({'f': 'json'}).encode("utf-8")
        request_url = self._feature_server_layer_url
        jsonResponse = json.loads(urllib.request.urlopen(request_url, parameters).read().decode("utf-8"))
        return jsonResponse

    def __get_feature_count(self):
        parameters = urllib.parse.urlencode({'where': '1=1',
                                             'returnCountOnly': 'true',
                                             'f': 'json'}).encode("utf-8")
        jsonResponse = json.loads(urllib.request.urlopen(self._feature_server_layer_url + '/{}/query?'.format(self.layer_id),
                                                         parameters).read().decode("utf-8"))
        return jsonResponse['count']

    @property
    def features(self, where='1=1', fields='*'):
        parameters = urllib.parse.urlencode({'where': where,
                                             'objectIds': '',
                                             'time': '',
                                             'geometry': '',
                                             'geometryType': 'esriGeometryEnvelope',
                                             'inSR': '',
                                             'spatialRel': 'esriSpatialRelIntersects',
                                             'relationParam': '',
                                             'outFields': fields,
                                             'returnGeometry': 'true',
                                             'maxAllowableOffset': '',
                                             'geometryPrecision': '',
                                             'outSR': '',
                                             'gdbVersion': '',
                                             'returnDistinctValues': 'false',
                                             'returnIdsOnly': 'false',
                                             'orderByFields': '',
                                             'groupByFieldsForStatistics': '',
                                             'outStatistics': '',
                                             'returnZ': 'false',
                                             'returnM': 'false',
                                             'f': 'json'}).encode("utf-8")
        request_url = self._feature_service_url + '/{}/query?'.format(self._layer_id)
        jsonResponse = json.loads(urllib.request.urlopen(request_url, parameters).read().decode("utf-8"))
        return jsonResponse

    @property
    def service_definition(self):
        return self._service_definition

    @property
    def service_definition_template(self):
        return self._service_definition_template

    @property
    def url(self):
        return self._feature_service_url

    @property
    def name(self):
        return self._name
    @property
    def layer_id(self):
        return self._layer_id

    @property
    def type(self):
        return self._type

    @property
    def feature_count(self):
        return self.__get_feature_count()


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
