#!/usr/bin/env /home/tops/bin/python
# -*- coding: utf-8 -*-
# Author: Ke Jie <jinxi.kj@taobao.com>
# Copyright (C) taobao.com 2013

'''
'''

import os
import sys
import json
import datetime

from unilog import unilogger as logger
from unilog import setup_rotating_log
from unilog import setup_console_log
import report
from mailer import Message
from mailer import Mailer

def define_options():
    import argparse
    parser = argparse.ArgumentParser(description='Loki Profile')
    parser.add_argument('-i', '--input',
            dest='input', default='./input',
            help='input data file, default: %(default)s')
    parser.add_argument('-o', '--output',
            dest='output', default='./output',
            help='check this(path or email) to enable html output, split emails with ";", default: %(default)s')
    parser.add_argument('-e', '--encoding',
            dest='encoding', default='utf-8',
            help='output encoding, default as %(default)s')
    parser.add_argument('-O', '--log-path',
            dest='log_path', default=None,
            help='path to runtime log')
    parser.add_argument('-q', '--quiet',
            action='store_false', dest='verbose', default=True,
            help='suppress automatic printing of runtime log')
    options = parser.parse_args()
    return options

class Reporter(object):
    def __init__(self, options):
        self._options = options
        self._data = None

        self._title = u'Loki运行状态报告-%s' % self.to_unicode(
                datetime.datetime.today().date() - datetime.timedelta(days=1))
        self._table_list = []

    def to_string(self, s, encoding='utf8'):
        result = ''
        if isinstance(s, unicode):
            result = s.encode(encoding, 'ignore')
        elif s == None:
            result = ''
        else:
            result = str(s)
        return result

    def to_unicode(self, s, encoding='utf8'):
        result = u''
        if s == None:
            return result
        if isinstance(s, unicode):
            return s
        result = str(s).decode(encoding, 'ignore')
        return result

    def number_to_human(self, s):
        result = ''
        chars = []
        for i, c in enumerate(str(s)[::-1]):
            if i > 0 and i%3 == 0:
                chars.append(',')
            chars.append(c)
        result = ''.join(chars[::-1])
        return result

    def _load_data(self, path):
        fp = open(path)
        content = fp.read().strip()
        fp.close()
        return json.loads(content)

    def start(self):
        self._data = self._load_data(self._options.input)

        self._add_summary_data()

        self._add_rt_data()

        self._add_match_rt_data()

        self._add_type_data()

        self._add_max_query_count()

        self._add_exception_data()

        self._add_description()

        self.report_text()

        self.report_html(self._options.output)

    def report_text(self):
        view = report.TextView(self._table_list, self._title)
        view.set_encoding(self._options.encoding)
        logger.info('show report as follow')
        for line in view.iterator():
            if line == None: continue
            logger.info(line)
        return

    def report_html(self, target):
        if not target:
            return
        view = report.HtmlView(self._table_list, self._title)
        view.set_encoding(self._options.encoding)
        if '@' in target:
            recp = []
            for mail_to in target.split(';'):
                mail_to = mail_to.strip()
                if not mail_to:
                    continue
                logger.info('send mail to %s', mail_to)
                recp.append(mail_to)
            msg = Message(
                    recp = recp,
                    subject = self._title,
                    html = view.show())
            mailer = Mailer()
            mailer.send(msg)
        else:
            path = os.path.abspath(target)
            logger.info('save html report in: %s', path)
            fp = open(path, 'wb')
            fp.write(view.show())
            fp.close()
        return

    def _add_summary_data(self):
        table = report.Table(title=u'概述', description=u'', key=u'目标', value=u'数量', show_total=False, show_percent=False)
        table.add_data('有效pv', self.number_to_human(self._data['ok_count']))
        table.add_data('平均qps(24小时)', self._data['qps_86400'])
        table.add_data('平均qps(5w秒)', self._data['qps_50000'])
        table.add_data('平均rt', '%.2f ms' % self._data['rt'])
        self._table_list.append(table)

    def _add_rt_data(self):
        table = report.Table(title=u'运行时间', description=u'系统平均RT性能数据分布', key=u'目标', value=u'数量(ms)', show_total=True, show_percent=True)
        table.add_data('match', self._data['match_rt'])
        table.add_data('rank', self._data['rank_rt'])
        table.add_data('other', self._data['rt'] - self._data['match_rt'] - self._data['rank_rt'])
        self._table_list.append(table)

    def _add_match_rt_data(self):
        table = report.Table(title=u'Match时间', description=u'Matching过程时间消耗明细', key=u'目标', value=u'数量(ms)', show_total=True, show_percent=True)
        table.add_data('match_rt', self._data['match_rt'])
        self._table_list.append(table)

    def _add_type_data(self):
        set = [
                ['2', '清单'],
                ['3', '专辑'],
                ['4', '搭配']
              ]
        for id, name in set:
            # title_conent = u'%s' %name
            # description_content = u'%s' %name
            table = report.Table(title=name, description=name, key=u'目标', value=u'数量', show_total = False, show_percent=False)
            table.add_data('pv', self.number_to_human(self._data['query_type'][id]))
            table.add_data('match_rt', self._data['match_time_type'][id])
            table.add_data('rank_rt', self._data['rank_time_type'][id])
            table.add_data('rt', self._data['rt_type'][id])
            table.add_data('succuess pv', self._data['success_pv_type'][id])
            table.add_data('failed pv', 0)
            if table.get_data_list():
                self._table_list.append(table)

    def _add_exception_data(self):
        table = report.Table(title=u'异常数据统计', description=u'无效日志等异常结果', key=u'目标', value=u'数量', show_total=False, show_percent=False)

        if self._data['failed_count'] > 0:
            table.add_data(u'无效日志', self._data['failed_count'])

        for key, count in self._data['status_count'].iteritems():
            if key == u'0':
                continue
            if count == 0:
                continue
            table.add_data(u'rank状态: %s' % self.to_unicode(key), count)

        if table.get_data_list():
            self._table_list.append(table)

    def _add_max_query_count(self):
        table = report.Table(title=u'峰值QPS',
                description=u'按时、分、秒关注峰值QPS，注：小时的峰值按照3600秒求平均，不考虑中途停止服务情况',
                key=u'目标', value=u'数量',
                show_total=False, show_percent=False)

        # hour
        max_timestamp = 0
        max_qps = 0
        for timestamp, qps in self._data[u'query_count_hour'].iteritems():
            timestamp = int(timestamp)
            if qps > max_qps:
                max_timestamp = timestamp
                max_qps = qps
        table.add_data(u'小时峰值发生时间, QPS', u'%s时, %.2f' % (str(datetime.datetime.fromtimestamp(max_timestamp))[:13], max_qps))
        # minute
        max_timestamp = 0
        max_qps = 0
        for timestamp, qps in self._data[u'query_count_minute'].iteritems():
            timestamp = int(timestamp)
            if qps > max_qps:
                max_timestamp = timestamp
                max_qps = qps
        table.add_data(u'分钟峰值发生时间, QPS', u'%s分, %.2f' % (str(datetime.datetime.fromtimestamp(max_timestamp))[:16], max_qps))
        # seconds
        max_timestamp = 0
        max_qps = 0
        for timestamp, qps in self._data[u'query_count'].iteritems():
            timestamp = int(timestamp)
            if qps > max_qps:
                max_timestamp = timestamp
                max_qps = qps
        table.add_data(u'秒级峰值发生时间, QPS', u'%s, %.2f' % (str(datetime.datetime.fromtimestamp(max_timestamp))[:19], max_qps))
        self._table_list.append(table)

    def _add_description(self):
        table = report.Table(title=u'备忘录', description=u'关于该报告的说明', key=u'选项', value=u'说明')
        table.add_data(u'联系人', u'萧亮(xiaoliang.zxl@taobao.com)')
        table.add_data(u'数据来源', u'Loki Profile日志，收集到云梯后，通过Hadoop计算得出;云梯路径: /group/tb-taoke-engine/logdata/aitaobao-profile/loki')
        table.add_data(u'其他', u'有任何疑问可以与上述联系人联系，请勿直接回复本邮件')
        self._table_list.append(table)

def main():
    ''' main function
    '''
    options = define_options()

    if options.verbose:
        setup_console_log()
    if options.log_path:
        setup_rotating_log(options.log_path)

    logger.info('send report from input data file: %s', options.input)

    report = Reporter(options)

    report.start()

    logger.info('done')

if __name__ == '__main__':
    main()
