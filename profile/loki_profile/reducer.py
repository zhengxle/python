#!/usr/bin/env /home/tops/bin/python
# -*- coding: utf-8 -*-
# Author: Ke Jie <jinxi.kj@taobao.com>
# Copyright (C) taobao.com 2013

'''
'''

import os
import sys
import json
import time
import datetime

class Reducer(object):
    def __init__(self):
        self._data = {
                'failed_count': 0,
                'ok_count': 0,
                'qps_86400': 0,
                'qps_50000': 0,
                'rt': 0,
                'rank_rt': 0,
                'match_rt': 0,
                'min_time': 0,
                'max_time': 0,
                'query_count': {},
                'query_count_minute': {},
                'query_count_hour': {},
                'query_type': {},
                'match_time_type': {},
                'rank_time_type': {},
                'rt_type': {},
                'sort_type':{},
                'result_type':{},
                'success_pv_type': {}
                }
        return

    def _process_ok_count(self, info):
        if not info['parse_ok_count']:
            return
        ok_count = info['parse_ok_count']
        self._data['ok_count'] = ok_count
        self._data['rt'] = float(info['rt_sum']) / ok_count
        self._data['rank_rt'] = float(info['rank_time_sum']) / ok_count
        self._data['match_rt'] = float(info['match_time_sum']) / ok_count
        self._data['qps_86400'] = ok_count / float(86400)
        self._data['qps_50000'] = ok_count / float(50000)

    def _process_query_count(self):
        for timestamp, count in self._data['query_count'].iteritems():
            t = datetime.datetime.fromtimestamp(timestamp)
            minute = datetime.datetime(t.year, t.month, t.day, t.hour, t.minute)
            hour = datetime.datetime(t.year, t.month, t.day, t.hour)
            if minute not in self._data['query_count_minute']:
                self._data['query_count_minute'][minute] = 0
            self._data['query_count_minute'][minute] += count
            if hour not in self._data['query_count_hour']:
                self._data['query_count_hour'][hour] = 0
            self._data['query_count_hour'][hour] += count

        qps_data = {}
        for key, value in self._data['query_count_minute'].iteritems():
            qps_data[int(time.mktime(key.timetuple()))] = float(value) / 60
        self._data['query_count_minute'] = dict(qps_data)
        qps_data = {}
        for key, value in self._data['query_count_hour'].iteritems():
            qps_data[int(time.mktime(key.timetuple()))] = float(value) / 60 / 60
        self._data['query_count_hour'] = dict(qps_data)

        return

    def start(self):
        info = {}
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            items = line.split('\t', 1)
            if len(items) != 2:
                continue
            key, value = items
            if key in ('parse_ok_count',
                    'parse_failed_count',
                    'rt_sum',
                    'match_time_sum',
                    'rank_time_sum',
                    'result_count'):
                value = float(value)
                if key not in info:
                    info[key] = value
                else:
                    info[key] += value
            if key == 'min_time':
                value = int(value)
                if self._data['min_time'] == 0:
                    self._data['min_time'] = value
                else:
                    self._data['min_time'] = min(self._data['min_time'], value)
            if key == 'max_time':
                value = int(value)
                self._data['max_time'] = max(self._data['max_time'], value)
            map_set = [
                    ['query_type_sum', 'query_type'],
                    ['sort_type_sum', 'sort_type'],
                    ['result_type_sum', 'result_type'],
                    ['match_time_type_sum', 'match_time_type'],
                    ['rank_time_type_sum', 'rank_time_type'],
                    ['rt_type_sum', 'rt_type'],
                    ['success_pv_type_sum', 'success_pv_type']
                    ]
            for map_key, reducer_key in map_set:
                if key == map_key:
                    value = json.loads(value)
                    for k, v in value.iteritems():
                        if k not in self._data[reducer_key]:
                            self._data[reducer_key][k] = 0
                        else:
                            self._data[reducer_key][k] += v

            if key == 'query_count_sum':
                value = json.loads(value)
                for timestamp, count in value.iteritems():
                    timestamp = int(timestamp)
                    if timestamp not in self._data['query_count']:
                        self._data['query_count'][timestamp] = 0
                    self._data['query_count'][timestamp] += count

        info['parse_ok_count'] = int(info['parse_ok_count'])

        self._process_ok_count(info)
        self._process_query_count()

        self._data['failed_count'] = int(info['parse_failed_count'])
        self._data['status_count'] = dict(self._data['result_type'])
        type_set = ['rank_time_type', 'match_time_type', 'rt_type']
        for type in type_set:
            self._data[type]['2'] = self._data[type]['2']/float(self._data['query_type']['2'])
            self._data[type]['3'] = self._data[type]['3']/float(self._data['query_type']['3'])
            self._data[type]['4'] = self._data[type]['4']/float(self._data['query_type']['4'])

        print json.dumps(self._data)

def main():
    ''' main function
    '''
    reducer = Reducer()
    reducer.start()

if __name__ == '__main__':
    main()
