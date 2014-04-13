#!/usr/bin/env /home/tops/bin/python
# -*- coding: utf-8 -*-
# Author: xiaoliang.zxl <xiaoliang.zxl@taobao.com>
# Copyright (C) taobao.com 2014

'''
'''

import os
import sys
import json

class OdinProfileParser(object):
    RANK_STATUS_DICT = {
            '-1': 'unused',
            '0': 'failed',
            '1': 'ok',
            }
    def __init__(self):
        return

    def parse(self, line):
        result = {}
        try:
            result = self._parse(line)
        except:
            result = {}
        return result

    def _parse(self, line):
        info = {}
        section = line.strip().split('\x01')
        if len(section) != 3:
            return None
        subsection = section[1].split('\x02')
        if len(subsection) != 6:
            return None
        info['timestamp'] = int(float(subsection[0]))
        info['pvid'] = subsection[1]
        info['biztype'] = subsection[2]
        info['offset'] = int(subsection[3])
        info['count'] = int(subsection[4])
        info['sortfactor'] = subsection[5]
        subsection2 = section[2].split('\x02')
        if len(subsection2) != 6:
            return None
        info['hostname'] = subsection2[0]
        info['retcode'] = subsection2[1]
        info['result_count'] = subsection2[2]
        info['doc_count'] = subsection2[3]
        info['match_time'] = float(subsection2[4]) / 1000.0
        info['rank_time'] = float(subsection2[5]) / 1000.0
        info['rt'] = float(info['match_time']) + float(info['rank_time'])
        return info

class Mapper(object):
    def __init__(self):
        self._parser = OdinProfileParser()

        self._parse_failed_count = 0
        self._parse_ok_count = 0

        self._rt_sum = 0
        self._match_time_sum = 0
        self._rank_time_sum = 0
        self._failed_pv_sum = 0
        self._success_pv_sum = 0

        self._rt_type_sum = {}
        self._match_time_type_sum = {}
        self._rank_time_type_sum = {}
        self._failed_pv_type_sum = {}
        self._success_pv_type_sum = {}
        self._result_type_sum = {}

        self._query_type_sum = {}
        self._sort_type_sum = {}
        self._query_count_sum = {}   # {timestamp: ...}
        self._result_count_sum = 0
        self._match_time_sum = 0
        self._rank_time_sum = 0
        self._min_time = 0
        self._max_time = 0

        self._max_qps = [] # {'time': .., 'qps': .., 'type': 'seconds'}
        self._doc_count = 0

    def start(self):
        for line in sys.stdin:
            line = line.strip()
            if line.startswith('0\t'):
                line = line[2:]
            if not line:
                continue
            info = self._parser.parse(line)
            if not info:
                self._parse_failed_count += 1
                continue
            self._add_info(info)
        self._show()

    def _show(self):
        args = {
                'parse_failed_count': self._parse_failed_count,
                'parse_ok_count': self._parse_ok_count,
                'rt_sum': self._rt_sum,
                'query_type_sum': json.dumps(self._query_type_sum),
                'sort_type_sum': json.dumps(self._sort_type_sum),
                'rt_type_sum': json.dumps(self._rt_type_sum),
                'result_type_sum': json.dumps(self._result_type_sum),
                'match_time_type_sum': json.dumps(self._match_time_type_sum),
                'rank_time_type_sum': json.dumps(self._rank_time_type_sum),
                'success_pv_type_sum': json.dumps(self._success_pv_type_sum),
                'failed_pv_type_sum': json.dumps(self._failed_pv_type_sum),
                'match_time_sum': self._match_time_sum,
                'rank_time_sum': self._rank_time_sum,
                'min_time': self._min_time,
                'max_time': self._max_time,
                'result_count': self._result_count_sum,
                'query_count_sum': json.dumps(self._query_count_sum)
                }
        for key, value in args.iteritems():
            print '%s\t%s' % (key, value)
        return

    def _add_info(self, info):
        info['timestamp'] = int(info['timestamp'])
        self._parse_ok_count += 1
        type_set = [
                self._query_type_sum,
                self._success_pv_type_sum,
                ]
        for type in type_set:
            if info['biztype'] not in type:
                type[info['biztype']] = 0
            else:
                type[info['biztype']] += 1
        time_type_set = [
                [self._rt_type_sum, 'rt'],
                [self._match_time_type_sum, 'match_time'],
                [self._rank_time_type_sum, 'rank_time']
                ]
        for type, seg in time_type_set:
            if info['biztype'] not in type:
                type[info['biztype']] = 0
            else:
                type[info['biztype']] += info[seg]

        if info['sortfactor'] not in self._sort_type_sum:
            self._sort_type_sum[info['sortfactor']] = 0
        else:
            self._sort_type_sum[info['sortfactor']] += 1

        if info['retcode'] not in self._result_type_sum:
            self._result_type_sum[info['retcode']] = 0
        else:
            self._result_type_sum[info['retcode']] += 1
        #if info['retcode'] != 0:
        #    if info['biztype'] not in type:
        #        self._failed_pv_type_sum[info['biztype']] = 0
        #    else:
        #        self._failed_pv_type_sum[info['biztype']] += 1

        self._result_count_sum += int(info['result_count'])
        self._doc_count += int(info['doc_count'])

        self._rt_sum += float(info['rt'])
        self._match_time_sum += float(info['match_time'])
        self._rank_time_sum += float(info['rank_time'])

        if self._min_time == 0:
            self._min_time = int(info['timestamp'])
        else:
            self._min_time = min(self._min_time, info['timestamp'])
        self._max_time = max(self._max_time, info['timestamp'])

        if info['timestamp'] not in self._query_count_sum:
            self._query_count_sum[info['timestamp']] = 0
        else:
            self._query_count_sum[info['timestamp']] += 1

def main():
    ''' main function
    '''
    mapper = Mapper()
    mapper.start()

if __name__ == '__main__':
    main()
