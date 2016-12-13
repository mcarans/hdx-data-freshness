#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
REGISTER:
---------

Caller script. Designed to call all other functions.

'''
import logging

from hdx.facades.simple import facade

from freshness import Freshness

logger = logging.getLogger(__name__)

def main(configuration):
    freshness = Freshness(configuration)
    metadata = freshness.process_datasets()
    results, hash_results = freshness.check_urls(metadata)
    datasets_lastmodified = freshness.process_results(results, hash_results)
    freshness.update_dataset_last_modified(datasets_lastmodified)
    freshness.output_counts()

if __name__ == '__main__':
    facade(main, hdx_site='prod')
