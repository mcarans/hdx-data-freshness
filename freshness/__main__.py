#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
REGISTER:
---------

Caller script. Designed to call all other functions.

'''
import argparse
import logging
import os

from hdx.configuration import Configuration
from hdx.logging import setup_logging

from freshness.freshness import Freshness

setup_logging()
logger = logging.getLogger(__name__)


def main(hdx_site, db_url, save):
    configuration = Configuration.create(hdx_read_only=True, hdx_site=hdx_site)
    logger.info('--------------------------------------------------')
    logger.info('> HDX Site: %s' % configuration.get_hdx_site_url())
    logger.info('> DB URL: %s' % db_url)
    freshness = Freshness(db_url=db_url, save=save)
    datasets_to_check, resources_to_check = freshness.process_datasets()
    results, hash_results = freshness.check_urls(resources_to_check)
    datasets_lastmodified = freshness.process_results(results, hash_results)
    freshness.update_dataset_last_modified(datasets_to_check, datasets_lastmodified)
    freshness.output_counts()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Data Freshness')
    parser.add_argument('-hs', '--hdx_site', default=None, help='HDX site to use')
    parser.add_argument('-db', '--db_url', default=None, help='Database connection string')
    parser.add_argument('-s', '--save', default=False, action='store_true', help='Save state for testing')
    args = parser.parse_args()
    hdx_site = args.hdx_site
    if hdx_site is None:
        hdx_site = os.getenv('HDX_SITE', 'prod')
    db_url = args.db_url
    if db_url is None:
        db_url = os.getenv('DB_URL')
    if '://' not in db_url:
        db_url = 'postgresql://%s' % db_url
    main(hdx_site, db_url, args.save)
