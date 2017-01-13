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
from ArcRESTAPI.AGOLHandler import *

def stringify(response_string):
    response_conversion = ''
    for word in response_string.split():
        new_word = word
        if word == 'true':
            new_word = '\"true\"'
        if word == 'false':
            new_word = '\"false\"'
        if word == 'none':
            new_word = '\"none\"'
        if word == 'true,':
            new_word = '\"true\",'
        if word == 'false,':
            new_word = '\"false\",'
        if word == 'none,':
            new_word = '\"none\",'
        response_conversion += (new_word + ' ')
    return response_conversion

class AGOLFeatureServer(object):
    """
    Wrapper around the AGOLHandler create service function.
    """
    def __init__(self, feature_server_url, feature_server_name, agol_handler=None):
        self._feature_server_url = feature_server_url
        self._feature_server_name = feature_server_name
        self._agol_handler = agol_handler
        self._service_definition = self.__service_definition()
        self._create_parameters_template = self.__create_parameters_template()
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
        with open(filename + '.json', 'w') as outfile:
            json.dump(returned_json, outfile, sort_keys=False, indent=4, ensure_ascii=False)

    def __service_definition(self):
        parameters = {'f': 'pjson'}
        if self._agol_handler is not None: parameters['token'] = self._agol_handler.token
        parameters = urllib.parse.urlencode(parameters).encode("utf-8")
        request_url = self._feature_server_url
        response = urllib.request.urlopen(request_url, parameters).read().decode("utf-8")
        jsonResponse = json.loads(stringify(response))
        jsonResponse['name'] = self._feature_server_name
        return jsonResponse

    def __create_parameters_template(self):
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
        self._layer_parameters_template = self.__layer_parameters_template()
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

    def __layer_parameters_template(self):
        """only need specific portions of the entire service definition to create a 'copy'"""
        layerParametersTemplate = {}
        layerParametersOptions = ['name', 'serviceDescription', 'hasStaticData', 'maxRecordCount', 'supportedQueryFormats',
                                  'capabilities', 'description', 'copyrightText', 'spatialReference', 'initialExtent',
                                  'allowGeometryUpdates', 'units', 'xssPreventionInfo']
        for paramater in layerParametersOptions:
            if paramater in self._service_definition:
                layerParametersTemplate[paramater] = self._service_definition[paramater]
        return layerParametersTemplate

    def __get_feature_count(self):
        parameters = urllib.parse.urlencode({'where': '1=1',
                                             'returnCountOnly': 'true',
                                             'f': 'json'}).encode("utf-8")
        jsonResponse = json.loads(urllib.request.urlopen(self._feature_server_layer_url + '/{}/query?'.format(self.layer_id),
                                                         parameters).read().decode("utf-8"))
        return jsonResponse['count']

    @property
    def query_features(self, where='1=1', fields='*'):
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
