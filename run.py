#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
REGISTER:
---------

Caller script. Designed to call all other functions.

'''
import logging
import time
import datetime

import asyncio

import async_timeout
import uvloop
import aiohttp
import hashlib
from dateutil import parser
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from hdx.data.resource import Resource
from hdx.facades.simple import facade

from database.base import Base
from database.dbresource import DBResource

logger = logging.getLogger(__name__)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
engine = create_engine('sqlite:///resources.db', echo=False)
Session = sessionmaker(bind=engine)
md5hash = hashlib.md5()

async def fetch(metadata, session):
    url, resource_id = metadata
    try:
        with async_timeout.timeout(10, loop=session.loop):
            async with session.get(url) as resp:
                logger.info(url)
                if resp.status != 200:
                    return resource_id, url, 0, resp.status
                last_modified = resp.headers.get('Last-Modified', None)
                if last_modified:
                    return resource_id, url, 1, last_modified
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        break
                    md5hash.update(chunk)
                return resource_id, url, 2, md5hash.hexdigest()
    except Exception as e:
        return resource_id, url, 0, str(e)

async def bound_fetch(sem, url, session):
    # Getter function with semaphore.
    async with sem:
        return await fetch(url, session)


async def check_resources_for_last_modified(last_modified_check, loop):
    tasks = list()

    # create instance of Semaphore
    sem = asyncio.Semaphore(100)

    conn = aiohttp.TCPConnector(conn_timeout=10, limit=10, keepalive_timeout=10)
    async with aiohttp.ClientSession(connector=conn, loop=loop) as session:
        for metadata in last_modified_check:
            task = asyncio.ensure_future(bound_fetch(sem, metadata, session))
            tasks.append(task)
        return await asyncio.gather(*tasks)


def set_last_modified(dbresource, modified_date):
    dbresource.http_last_modified = parser.parse(modified_date, ignoretz=True)
    if dbresource.last_modified:
        if dbresource.http_last_modified > dbresource.last_modified:
            dbresource.last_modified = dbresource.http_last_modified
    else:
        dbresource.last_modified = dbresource.http_last_modified


def main(configuration):
    ''''''
    Base.metadata.create_all(engine)
    session = Session()
    resources = Resource.search_in_hdx(configuration, 'name:')
    total = len(resources)
    datahumdataorg_count = 0
    managehdxrwlabsorg_count = 0
    proxyhxlstandardorg_count = 0
    scraperwikicom_count = 0
    ourairportscom_count = 0
    last_modified_check = list()
    for resource in resources:
        resource_id = resource['id']
        url = resource['url']
        name = resource['name']
        revision_last_updated = resource.get('revision_last_updated', None)
        if revision_last_updated:
            revision_last_updated = parser.parse(revision_last_updated, ignoretz=True)
        dbresource = session.query(DBResource).filter_by(id=resource_id).first()
        if dbresource is None:
            dbresource = DBResource(id=resource_id, name=name, url=url,
                                    last_modified=revision_last_updated, revision_last_updated=revision_last_updated)
            session.add(dbresource)
        else:
            dbresource.name = name
            dbresource.url = url
            dbresource.last_modified = revision_last_updated
            dbresource.revision_last_updated = revision_last_updated
        if 'data.humdata.org' in url:
            datahumdataorg_count += 1
            continue
        if 'manage.hdx.rwlabs.org' in url:
            managehdxrwlabsorg_count += 1
            continue
        if 'proxy.hxlstandard.org' in url:
            proxyhxlstandardorg_count += 1
            continue
        if 'scraperwiki.com' in url:
            scraperwikicom_count += 1
            continue
        if 'ourairports.com' in url:
            ourairportscom_count += 1
            continue
        last_modified_check.append((url, resource_id))
    session.commit()
    last_modified_check = sorted(last_modified_check)
    start_time = time.time()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(check_resources_for_last_modified(last_modified_check, loop))
    results = loop.run_until_complete(future)
    logger.info('Execution time: %s seconds' % (time.time() - start_time))
    lastmodified_count = 0
    hash_updated_count = 0
    hash_unchanged_count = 0
    failed_count = 0
    for resource_id, url, status, result in results:
        dbresource = session.query(DBResource).filter_by(id=resource_id).first()
        if status == 0:
            failed_count += 1
            dbresource.error = result
        elif status == 1:
            lastmodified_count += 1
            set_last_modified(dbresource, result)
        elif status == 2:
            if dbresource.md5_hash == result:  # File unchanged
                hash_unchanged_count += 1
            else:  # File updated
                dbresource.md5_hash = result
                dbresource.last_hash_date = datetime.datetime.utcnow()
                hash_updated_count += 1
        else:
            raise ValueError('Invalid status returned!')
    session.commit()
    str = '\ndata.humdata.org: %d, manage.hdx.rwlabs.org: %d, ' % (datahumdataorg_count, managehdxrwlabsorg_count)
    str += 'proxy.hxlstandard.org: %d, scraperwiki.com: %d, ' % (proxyhxlstandardorg_count, scraperwikicom_count)
    str += 'ourairports.com: %d\n' % ourairportscom_count
    str += 'Have Last-Modified: %d, Hash updated: %d, ' % (lastmodified_count, hash_updated_count)
    str += 'Hash Unchanged: %d\n' % hash_unchanged_count
    str += 'Number Failed: %d, Total number: %d' % (failed_count, total)
    logger.info(str)

if __name__ == '__main__':
    facade(main, hdx_site='prod')
