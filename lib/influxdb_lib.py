#!/usr/bin/env python3


###
# Library to connect to InfluxDB via Python SDK and write measurements time
# series data to DB and fetch data
# Author - venksrin@pensando.io
###

from influxdb import InfluxDBClient
import sys
import os
import re
import logging
import json

import time
import datetime
#from datetime import datetime





class influxDBClient():

    def __init__(self, log, host, username='root', password = 'docker', port=8086 ):


        self.log         = log
        self.host        = host
        self.username    = username
        self.password    = password
        self.port        = port
        self.client      = None
        self.current_db  = None

        try:
            self.client = InfluxDBClient( host=self.host, port=self.port, username=self.username,
                          password=self.password )
        except Exception as e:
            self.log.error('ERROR connecting to Influx DB on Host {} - exception {}'.format(self.host, e ))
       


    def get_db_list( self, ):
        db_list = self.client.get_list_database()
        return db_list


    def create_db( self, dbname, retention_duration, replication ):
        try: 
           self.client.create_database(dbname)
        except Exception as e:
           self.log.error('ERROR creating DB {} on host {} - Exception {}'.format(db_name, self.host, e ) )
           return

        retention_policy_name = dbname + "_retention_policy"
        client.create_retention_policy( retention_policy_name, database=dbname, duration=retention_duration, replication=replication )
        db_list = self.get_db_list()
        if db_name not in db_list:
           self.log.error('ERROR DB {} not created on host {}'.format( db_name, self.host ))


    def switch_db( self, db_name ):
        self.log.info('Switching to DB {}'.format(db_name))
        self.client.switch_database(db_name)
        self.current_db = db_name


    def write_measurement_point( self, db_name, measurement_name, json_string ):

        # Make sure you add the tags and time fields in the Json_string when you write
        if self.current_db != db_name:
           self.switch_db( db_name )

        self.log.info( 'Writing Measurement {} to DB {}'.format( measurement_name, db_name ))
        json_body = eval(json_string)
        print(json_body)
        resp = self.client.write_points(json_body)
        if resp is not True:
           self.log.error('Write Measurement {} to DB {} failed'.format( measurement_name, db_name, e))
           print('ERROR Write Measurement {} to DB {} failed'.format( measurement_name, db_name, e))


    def query_points_for_last_x_mins( self, db_name, measurement_name, field_list, tag_name, duration_in_min ):

        if self.current_db != db_name:
           self.switch_db( db_name )

        time_since_obj = datetime.datetime.now() - datetime.timedelta(minutes=duration_in_min)
        time_since = datetime.datetime.strftime( time_since_obj, '%Y-%m-%dT%H:%M:%S.%fZ' ) 
        #time_since = datetime.datetime.strftime( time_since_obj, '%Y-%m-%dT%H:%M:%SZ' ) 

        query_cmd = '''SELECT {} FROM "{}"."autogen"."{}" WHERE time >= '{}' GROUP BY "{}"'''.format(
                     field_list, db_name, measurement_name, time_since, tag_name )
        print(query_cmd)
        result = self.client.query(query_cmd)
        return result.raw


    def convert_raw_points_to_dict(self, result, tag_name ):
        # This is done to be able to feed the data easily to Google charts
        # The dict should be organized as node as top level key, then timestamp and value ..
        out_dict = {}
        for series_dict in result['series']:
            node = series_dict['tags'][tag_name]
            out_dict[node] = {}
            for val_list in series_dict['values']:
                print(val_list[0])
                if re.search( '[0-9\-]+T([0-9][0-9]:[0-9][0-9]:[0-9][0-9])\.[0-9]+Z', val_list[0] ):
                   match = re.search('[0-9\-]+T([0-9][0-9]:[0-9][0-9]:[0-9][0-9])\.[0-9]+Z', val_list[0] )
                elif re.search( '[0-9\-]+T([0-9][0-9]:[0-9][0-9]:[0-9][0-9])Z', val_list[0] ):
                   match = re.search( '[0-9\-]+T([0-9][0-9]:[0-9][0-9]:[0-9][0-9])Z', val_list[0] )
                timestamp = match.group(1)
                 
                out_dict[node][timestamp] = val_list[1:]
        print(out_dict) 
        return out_dict 
    
     
    def convert_raw_points_to_dict_of_x_elements(self, result, tag_name, x=10 ):
        # This is done to be able to feed the data easily to Google charts
        # The dict should be organized as node as top level key, then timestamp and value ..
        # will return only x elements in that range
        out_dict = {}
        for series_dict in result['series']:
            node = series_dict['tags'][tag_name]
            out_dict[node] = {}
            value_list = series_dict['values']
            if len(value_list) < x:
               index_incrementor = x
            else:
               index_incrementor = int(len(value_list)/x)
            for i in range( 0, len(value_list), index_incrementor ):
                val_list = series_dict['values'][i]
                print(val_list[0])
                if re.search( '[0-9\-]+T([0-9][0-9]:[0-9][0-9]:[0-9][0-9])\.[0-9]+Z', val_list[0] ):
                   match = re.search('[0-9\-]+T([0-9][0-9]:[0-9][0-9]:[0-9][0-9])\.[0-9]+Z', val_list[0] )
                elif re.search( '[0-9\-]+T([0-9][0-9]:[0-9][0-9]:[0-9][0-9])Z', val_list[0] ):
                   match = re.search( '[0-9\-]+T([0-9][0-9]:[0-9][0-9]:[0-9][0-9])Z', val_list[0] )
                timestamp = match.group(1)
                 
                out_dict[node][timestamp] = val_list[1:]
        print(out_dict) 
        return out_dict 
         
         

# Crude hack to convert time stamp format for Graph to just use the hour, min, sec.
         

# Crude hack to convert time stamp format for Graph to just use the hour, min, sec.
def convert_timestamp_fmt_in_points( input_dict ):
    output_dict = {}
    for series_dict in input_dict['series']:
        node_name = series_dict['tags']['psm-node']
        output_dict[node_name] = {}
        output_dict[node_name]['columns'] = series_dict['columns']
        value_list = []
        for val_list in series_dict['values']:
            tmp_list = []
            for val in val_list:
                if isinstance(val, str ):
                   if re.search( '[0-9\-T]+[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.[0-9Z]+', val ):
                      match = re.search( '[0-9\-T]+([0-9][0-9]:[0-9][0-9]:[0-9][0-9])\.[0-9Z]+', val )
                      new_val = match.group(1)
                   else:
                      new_val = val
                else:
                   new_val = val
                tmp_list.append(new_val)
            value_list.append(tmp_list)
        output_dict[node_name]['values'] = value_list
    print(output_dict)
    return output_dict

        
        

