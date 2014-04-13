#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: 柯杰(金喜) <jinxi.kj@taobao.com>
# Copyright (C) taobao.com 2011

''' report tables
'''

import os
import sys

class Table(object):
    STRING_OTHERS = u'其他'
    def __init__(self, title=u'', key=u'', value=u'',
            show_total=False, description=None, limit=None,
            show_percent=False, should_sort=True, reverse_sort=True):
        self._title = title
        self._key_name = key
        self._value_name = value
        self._description = description
        self._limit = limit
        self._show_total = show_total
        self._show_percent = show_percent

        self._sort = should_sort
        self._reverse = reverse_sort

        self._data = []
        self._is_number = True
        return

    def add_data(self, key, value):
        if not isinstance(value, int) and not isinstance(value, float):
            self._is_number = False
        self._data.append((key, value))

    def get_title_list(self):
        result = [self._key_name, self._value_name]
        if self._show_percent:
            result.append(u'比例')
        return list(result)

    def get_data_list(self):
        result = []

        # create line template
        base_item = [None, None]
        if self._show_percent: base_item.append(None)

        # fill raw data
        total = 0
        for key, value in self._data:
            if self._show_total or self._show_percent: total += value
            new_item = list(base_item)  # create new instance with list()
            new_item[0], new_item[1] = (key, value)
            result.append(new_item)

        # sort
        if self._is_number and self._sort:
            result = sorted(result, key=lambda x:x[1], reverse=self._reverse)

        # limit
        if self._is_number and self._limit and self._limit > 1 and self._limit < len(result):
            others_item = list(base_item)
            others_item[0] = self.STRING_OTHERS
            others_item[1] = sum([i[1] for i in result[self._limit:]])
            result = result[:self._limit] + [others_item]

        # fill percent rate
        if self._show_percent:
            for index in xrange(len(result)):
                items = result[index]
                rate = 0.0
                if total != 0: rate = items[1] / float(total)
                items[2] = rate

        # fill total
        if self._show_total:
            total_items = list(base_item)
            total_items[0], total_items[1] = u'total', total
            if self._show_percent: total_items[2] = 1
            result.append(total_items)

        return list(result)

    def get_table_matrix(self):
        result = []

        title_list = self.get_title_list()

        data_list = self.get_data_list()

        result.append(title_list)
        result += data_list

        return list(result)


class View(object):
    SEPARATOR_LENGTH = 32
    def __init__(self, table_list = [], title=u'View Title'):
        self._title = title
        self._table_list = table_list
        self._encoding = 'utf8'
        return

    def set_encoding(self, encoding):
        self._encoding = encoding

    def iterator(self):
        yield None

    def _(self, s):
        result = ''
        if isinstance(s, unicode):
            result = self.to_string(s, self._encoding)
        elif isinstance(s, str):
            result = s
        elif isinstance(s, float):
            result = str(round(s, 2))
        else:
            result = str(s)
        return result

    def show(self):
        result = ''
        line_list = []
        for line in self.iterator():
            if line == None: continue
            line_list.append(line)
        result = '\n'.join(line_list)
        return result

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

    def _percent(self, rate):
        if rate == 0:
            return self._(u'0%')
        if rate == 1:
            return self._(u'100%')
        if isinstance(rate, int):
            rate = float(rate)
        if not isinstance(rate, float):
            return self._(u'-')
        result = str(round(rate * 100, 2)) + '%'
        return result


class TextView(View):
    def _big_separator(self, _length = None):
        length = self.SEPARATOR_LENGTH
        if _length: length = _length
        return '=' * length

    def _separator(self, _length = None):
        length = self.SEPARATOR_LENGTH
        if _length: length = _length
        return '-' * length

    def _get_line(self, items, _lengths, convert_rate = False):
        result = [None] * len(items)
        lengths = list(_lengths)

        while len(lengths) < len(items):
            lengths.append(False)    # indicate as no just

        new_items = list(items)
        # fill key & value
        new_items[0], new_items[1] = self._(new_items[0]), self._(new_items[1])
        # fill rate
        if len(new_items) >= 3:
            if convert_rate:
                new_items[2] = self._percent(new_items[2])
            else:
                new_items[2] = self._(new_items[2])
        # just
        for i in xrange(len(new_items)):
            if i >= len(lengths): break
            length = lengths[i]
            if not length: continue
            new_items[i] = new_items[i].ljust(length)
        result = ' '.join(new_items)
        return result

    def iterator(self):
        yield self._(self._title)

        is_first = True
        for table in self._table_list:
            if is_first: yield self._big_separator()
            is_first = False

            # table title
            title = 'Title: %s' % self._(table._title)
            yield title
            yield '-' * len(title)
            # description
            if table._description != None:
                yield 'Description: %s' % self._(table._description)
            # table items
            header = table.get_title_list()
            body = table.get_data_list()
            matrix = table.get_table_matrix()
            # fields length
            key_length = max([len(self._(items[0])) for items in matrix]) + 2
            value_length = max([len(self._(items[1])) for items in matrix]) + 2
            # yield head
            yield self._get_line(header, (key_length, value_length), convert_rate=False)
            # yield body
            count = 0
            for items in body:
                line = self._get_line(items, (key_length, value_length), convert_rate=True)
                count += 1

                if table._show_total and count == len(body):  # is total
                    yield self._separator(len(line))
                yield line
            yield self._big_separator()

        yield None
        # the end

class HtmlView(View):
    DEFAULT_CSS = """
body
{
    line-height: 1.6em;
}
h1
{
    text-align: left;
    color: #039;
    margin-left: 45px;
}
.beautify
{
    font-family: "Lucida Sans Unicode", "Lucida Grande", Sans-Serif;
    font-size: 12px;
    background: #fff;
    /* margin: 45px; */
    width: 480px;
    border-collapse: collapse;
    text-align: left;
}
.beautify caption
{
    font-size: 16px;
    font-weight: bold;
    color: #039;
    padding: 10px 8px;
}
.beautify th
{
    font-size: 14px;
    font-weight: normal;
    color: #039;

    padding: 10px 8px;
    border-bottom: 2px solid #6678b1;
}
.beautify td
{
    color: #669;
    padding: 9px 8px 0px 8px;
}
.beautify tbody tr:hover td
{
    color: #009;
}
    """
    def iterator(self):
        yield self._('<html>')
        yield self._('<head>')
        yield '    <meta http-equiv="content-type" content="text/html;charset=%s" />' % self._(self._encoding)
        yield '    <title>%s</title>' % self._(self._title)
        yield '    <style type="text/css">'
        for line in self.DEFAULT_CSS.strip().split('\n'):
            yield '        %s' % self._(line)
        yield '    </style>'
        yield self._('</head>')
        yield self._('<body>')
        yield self._('<div id="wrapper">')
        yield '    <h1>%s</h1>' % self._(self._title)
        for table in self._table_list:
            yield self._('    <table class="beautify">')
            yield self._('        <caption>')
            if table._description:
                yield '            %s | %s' % (self._(table._title), self._(table._description))
            else:
                yield '            %s' % self._(table._title)
            yield self._('        </caption>')

            yield self._('        <thead><tr>')
            for i in table.get_title_list():
                yield '            <th scope="col" class="beautify">%s</th>' % self._(i)
            yield self._('        </tr></thead>')

            total = 0
            yield self._('        <tbody>')
            for _fields in table.get_data_list():
                fields = list(_fields)
                if len(fields) >= 3 and table._show_percent:
                    fields[2] = self._percent(fields[2])
                yield self._('        <tr>')
                for i in fields:
                    yield '            <td>%s</td>' % self._(i)
                yield self._('        </tr>')

            yield self._('        </tbody>')
            yield self._('    </table>')
        yield self._('</div>')
        yield self._('</body>')
        yield self._('</html>')

def main():
    ''' main function '''
    print 'Done'

if __name__ == '__main__':
    main()
