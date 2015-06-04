"""
Garbo AWS discovery configuration
"""
import os
access_key = os.environ['AMAZON_ACCESS_KEY_ID']
secret_access_key = os.environ['AMAZON_SECRET_ACCESS_KEY']

# which regions to discover, set to [] for all regions
regions = ['us-east-1', 'eu-west-1']
