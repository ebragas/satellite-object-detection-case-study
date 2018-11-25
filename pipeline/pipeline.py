#!/usr/bin/env python

from planet_filters import planet_filter
'''
Primary components:
1. Search for additional scenes
2. Write scene metadata to DataStore
3. Download images from metadata; mark entity as downloaded
4. Preprocess and annotate images; store annotated image; mark entity as annotated with image public URL
'''

import os
import json
import requests
import logging
from time import sleep
from requests.auth import HTTPBasicAuth
from datetime import datetime
from utils import *
from pprint import pprint
from glob import glob
from google.cloud.datastore.helpers import GeoPoint

logging.basicConfig(level=logging.DEBUG)


# Planet search filters
logging.info('Loaded planet filters')

if __name__ == "__main__":

    run_start = datetime.now()

    # ------------------------ Planet API ---------------------------- #

    FILTER_NAME = 'sf_bay'
    ITEM_TYPES = ['PSScene3Band']
    DAYS = 1
    MAX_CLOUD_COVER = 0.5

    # Load checkpoints
    checkpoint_dir = create_tmp_dir(directory_name='tmp')
    
    stats_response = maybe_load_from_checkpoint(checkpoint_dir, 'stats_response.json')
    search_response = maybe_load_from_checkpoint(checkpoint_dir, 'search_response.json')
    feature_assets = maybe_load_from_checkpoint(checkpoint_dir, 'feature_assets.json')


    # Get search stats
    if not stats_response: # TODO: improve search by filtering date > newest entity in DataStore
        stats_response = planet_stats_endpoint_request(item_types=ITEM_TYPES,
                                                    filter_name=FILTER_NAME,
                                                    days=DAYS,
                                                    max_cloud_cover=MAX_CLOUD_COVER)

        write_to_checkpoint(checkpoint_dir, 'stats_response.json', stats_response)

    num_avail_scenes = sum([bucket['count'] for bucket in stats_response['buckets']])


    # Get features with search endpoint
    if not search_response:
        search_response = planet_quick_search_endpoint_request(item_types=ITEM_TYPES,
                                                               filter_name=FILTER_NAME,
                                                               days=DAYS,
                                                               max_cloud_cover=MAX_CLOUD_COVER)
        
        write_to_checkpoint(checkpoint_dir, 'search_response.json', search_response)

    # Check response quality
    feature_list = search_response.get('features', [])
    if len(feature_list) < num_avail_scenes:
        logging.warn("Additional features are available but were missed because paging isn't implemented yet!")
    

    # Get item assets
    if not feature_assets:
        for feature in feature_list:
            if not feature.get('assets', {}):
                # TODO: make sure this is working as intended; wasn't returning anything before
                assets = planet_get_item_assets(item=feature, item_type=ITEM_TYPES[0])
                feature['assets'] = assets
                sleep(3)

        write_to_checkpoint(checkpoint_dir, 'feature_assets.json', feature_list)



    # ------------------------ Load to DataStore ---------------------------- #

    ENTITY_KIND = 'PlanetScenes'

    # convert coordinates to GeoPoints
    for feature in feature_list:
        feature['geometry']['coordinates'] = convert_coord_list_to_geopoints(
            feature['geometry']['coordinates'][0])

        # NOTE: assumes we only get one geometry, causes intentional data loss otherwise

    # Upsert entities to DataStore
    feature_ids = [feature.pop('id') for feature in feature_list]
    datastore_batch_upsert(feature_list, ENTITY_KIND, feature_ids)


    run_end = datetime.now()
    logging.info('')
    logging.info('Pipeline completed:\t{}'.format(datetime.now()))
    logging.info('Total runtime:\t{}'.format(run_end - run_start))
