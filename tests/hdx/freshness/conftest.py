# -*- coding: UTF-8 -*-
"""Global fixtures"""
from collections import UserDict
from os.path import join

import pytest
from hdx.hdx_configuration import Configuration


@pytest.fixture(scope='session')
def configuration():
    project_config_yaml = join('src', 'hdx', 'freshness', 'project_configuration.yml')
    Configuration._create(hdx_site='prod', user_agent='test', hdx_read_only=True,
                          project_config_yaml=project_config_yaml)


@pytest.fixture(scope='session')
def resourcecls():
    class MyResource(UserDict, object):
        touched = False
        resourcedict = None

        def __init__(self, id):
            self.data = self.resourcedict[id]

        @classmethod
        def populate_resourcedict(cls, datasets):
            cls.resourcedict = dict()
            for dataset in datasets:
                for resource in dataset.get_resources():
                    cls.resourcedict[resource['id']] = resource

        @staticmethod
        def read_from_hdx(id):
            return MyResource(id)

        @classmethod
        def update_in_hdx(cls, operation, batch_mode, skip_validation, ignore_check):
            cls.touched = True

    return MyResource
