# -*- coding: utf-8 -*-
'''
Unit tests for the serializing code.

'''
import datetime
import os
import pickle
from os.path import join

import pytest
from hdx.utilities.database import Database

from hdx.freshness.testdata.serialize import serialize_datasets, deserialize_datasets, serialize_now, deserialize_now, \
    serialize_results, deserialize_results, serialize_hashresults, deserialize_hashresults


class TestSerialize:
    @pytest.fixture(scope='function')
    def session(self):
        dbpath = join('tests', 'test_serialize.db')
        try:
            os.remove(dbpath)
        except FileNotFoundError:
            pass
        return Database.get_session('sqlite:///%s' % dbpath)

    @pytest.fixture(scope='function')
    def datasets(self):
        fixture = join('tests', 'fixtures', 'datasets.pickle')
        with open(fixture, 'rb') as fp:
            return pickle.load(fp)

    def test_serialize_datasets(self, configuration, session, datasets):
        serialize_datasets(session, datasets)
        for i, result in enumerate(deserialize_datasets(session)):
            dataset = datasets[i]
            assert result['organization']['id'] == dataset['organization']['id']
            assert result['organization']['name'] == dataset['organization']['name']
            assert result['organization']['title'] == dataset['organization']['title']
            assert result['name'] == dataset['name']
            assert result['title'] == dataset['title']
            assert result['private'] == dataset['private']
            assert result['maintainer'] == dataset['maintainer']
            assert result['maintainer_email'] == dataset['maintainer_email']
            assert result['author'] == dataset['author']
            assert result['author_email'] == dataset['author_email']
            assert result['dataset_date'] == dataset.get('dataset_date')
            assert result['metadata_modified'] == dataset['metadata_modified']
            assert result['data_update_frequency'] == dataset.get('data_update_frequency')
            assert result['is_requestdata_type'] == dataset.get('is_requestdata_type')
            assert result['groups'] == [{'name': x['name']} for x in dataset.get('groups')]
            resources = dataset.get_resources()
            for j, result_resource in enumerate(result.get_resources()):
                resource = resources[j]
                assert result_resource['id'] == resource['id']
                assert result_resource['name'] == resource['name']
                assert result_resource['format'] == resource['format']
                assert result_resource['url'] == resource['url']
                assert result_resource['revision_last_updated'] == resource['revision_last_updated']

    def test_serialize_now(self, session):
        now = datetime.datetime.utcnow()
        serialize_now(session, now)
        result = deserialize_now(session)
        assert result == now

    def test_serialize_results(self, session):
        results = {'c001c17e-92e1-4c15-ac7f-e9a2a22bc11e': (
            'http://siged.sep.gob.mx/SIGED/content/conn/WCPortalUCM/path/Contribution%20Folders/PortalSIGED/Descargas/Datos%20Abiertos/Censo/Personal/Cuestionarios/PERSONAL_CUES_CT_CENSADOS.zip',
            'code=404 message=Non-retryable response code raised=aiohttp.errors.HttpProcessingError url=http://siged.sep.gob.mx/SIGED/content/conn/WCPortalUCM/path/Contribution%20Folders/PortalSIGED/Descargas/Datos%20Abiertos/Censo/Personal/Cuestionarios/PERSONAL_CUES_CT_CENSADOS.zip',
            None, None, False),
            '563e2bd1-b200-416b-99be-425777ad686a': (
                'http://geonode.state.gov/geoserver/wms/kml?layers=geonode%3ASyria_BorderCrossings_2015Jun11_HIU_USDoS&mode=download',
                None, None, 'bde2adc82876bd845cc4c5233c224a10', False),
            'a9cb1b9e-93b2-4ff4-82a7-3aab8b13d7b6': (
                'http://www.majidata.go.ke/dataset_dl.php?meza=H_County_WaterSupply_ALinked', None, None,
                '1a1e0af350ac825ba21adefd94926c9d', False)
        }
        serialize_results(session, results)
        result = deserialize_results(session)
        assert result == results

    def test_serialize_hash_results(self, session):
        hash_results = {'dc8da7da-59bc-4fad-98b8-9a0303b2deed': (
            'http://data.humdata.org/dataset/e66dbc70-17fe-4230-b9d6-855d192fc05c/resource/dc8da7da-59bc-4fad-98b8-9a0303b2deed/download/myanmar-adm2.geojson',
            None, datetime.datetime(2015, 7, 24, 7, 8, 48), '73ba2b7904c778ed218357d9c1515c0c', True),
            '3eb2c0ac-4b27-49b6-be25-f5ccb7128d65': (
                'http://sddr.faoswalim.org/Shapefiles/Administrative/Somalia%20Major%20Primary%20Roads.ZIP',
                None, datetime.datetime(2013, 2, 28, 13, 53, 42), '3e59e8be4973de25eaa4283e075ad5b2', True),
            'e3eea5de-80bf-4b2a-9729-31b89d6fb36c': (
                'http://ourairports.com/countries/RS/airports.hxl', None, None,
                '71d1ecb069dbd2fc32f79eb6e0859c55', True),
            'e351d04f-fade-45f9-81fa-0ea673bd9b33': (
                'https://docs.google.com/spreadsheets/d/1kPO1CmPvc42j9TouovP5tyiSdegRk1wISLpxMWDlfaQ/pub?gid=0&single=true&output=csv',
                None, None, '6827a97f982da889840d03f568a04f32', False)}
        serialize_hashresults(session, hash_results)
        result = deserialize_hashresults(session)
        assert result == hash_results
