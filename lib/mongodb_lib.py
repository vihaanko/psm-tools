#!/usr/bin/env python3


###
# Library to connect to MongoDB and write the information collected by our polling scripts
# for the data to be used by the smashing dashboards
#
# Author - venksrin@pensando.io
###

import os
import re
import pymongo
from pymongo import MongoClient
import logging




class mongoClientObj():


    def __init__(self, log, host_addr, username='admin', password='docker', port=27017 ):

        self.log              = log
        self.host_addr        = host_addr
        self.port             = port
        self.username         = username
        self.password         = password

        self.client           = None
        self.db               = None
        self.collection       = None
        self.client  = MongoClient( self.host_addr, self.port, username=self.username, password=self.password,
                       authSource='admin', authMechanism='SCRAM-SHA-1')



    def get_database_list(self, ):
        print(self.client.list_database_names())
        return self.client.list_database_names()


    def get_collection_list(self, db_name ):
        self.db = self.client[db_name]
        print(self.db.list_collection_names())
        return self.db.list_collection_names()


    def create_database( self, db_name ):
        self.db = self.client[db_name]
        print(self.client.list_database_names())


    def create_collection( self, db_name, collection_name ):
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        

    def switch_db( self, db_name ):
        self.db = self.client[db_name]


    # Returns a list of dict_items - key and values .. Single record ..
    # Return it as a dictionary ..
    def get_record( self, collection_name, query_json ):
        record_dict = {}
        self.collection = self.db[collection_name]
        doc_list = self.collection.find(query_json)
        print(doc_list[0].items())
        for k,v in doc_list[0].items():
            record_dict[k] = v 
        return record_dict


    # Returns a list of list of dict_items - Multiple records ..
    # Returns a list of dictionaries ..
    def get_records( self, collection_name, query_json ):
        record_items = []
        self.collection = self.db[collection_name]
        doc_list = self.collection.find(query_json)
        for doc in doc_list:
            out_dict = {}
            for k,v in doc.items():
                out_dict[k] = v
            record_items.append(out_dict)
        return record_items


    # Insert a single record to a Collection within a DB ..
    def insert_record( self, collection_name, json_str ):
        self.collection = self.db[collection_name]
        post_id = self.collection.insert_one(json_str).inserted_id
        print(post_id)



    # Update an existing record in a collection ..
    def update_record( self, collection_name, query_json, update_json ):
        self.collection = self.db[collection_name]
        update_set_json = { "$set": update_json }
        self.collection.update_one( query_json, update_set_json )
         





# Sample Usage ...
#logging.basicConfig( level=logging.INFO, filename="/tmp/venk_script.log", filemode='w')
#logging.root.setLevel(logging.INFO)
#log = logging.getLogger("mon")
#mc = mongoClientObj( log, 'localhost', )
#mc.get_database_list()
#mc.get_collection_list('test-database')
#mc.create_database( 'car-metrics' )
#mc.get_database_list()
#mc.create_collection( 'car-metrics', 'price' )
#mc.switch_db( 'car-metrics')
#mc.insert_record( 'price', { "car-make": "benz", "price": 100 } )
#mc.get_records( 'price', { "car-make": "benz" } )
#mc.update_record( 'price', { "car-make": "benz" }, { "car-make": "benz", "price": 500 } )
#mc.get_record( 'price', { "car-make": "benz" } )
