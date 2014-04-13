#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Ke Jie <jinxi.kj@taobao.com>
# Copyright (C) taobao.com 2011

''' simple mail module in Python
send email simply, support attachments, unicode and /usr/sbin/sendmail(8).

Released under MIT license.

Thanks for Ryan Ginstrom's work: http://ginstrom.com/code/mailer.html and 
Python email module document: http://docs.python.org/library/email-examples.html

Features
- support both smtp directly and /usr/sbin/sendmail(8)
- support attachments
- support unicode
- support html
- support default sender(user@hostname)

Example
1. basic
    msg = Message(recp = ['foo@bar.com'], subject='hello', text='world') 
    mailer = Mailer()
    mailer.send(msg)
2. send html mail
    msg = Message(recp = ['foo@bar.com'], subject='hello', html='<html><body>world</body></html>') 
    mailer = Mailer()
    mailer.send(msg)
3. attachments
    msg = Message(recp = ['foo@bar.com'], subject='hello', text='world', attachments=['/etc/foobar']) 
    mailer = Mailer()
    mailer.send(msg)
4. importance(high or low)
    msg = Message(recp = ['foo@bar.com'], subject='hello', text='world', importance='high') 
    mailer = Mailer()
    mailer.send(msg)
5. send with smtp directly
    msg = Message(sender='foobar@example.com', recp = ['foo@bar.com'], subject='hello', text='world')
    mailer = Mailer('mail.example.com')
    mailer.login('foobar@example.com', 'password')
    mailer.send(msg)
'''

import os
import sys
import time
import socket
import getpass
import smtplib

try:
    from email import encoders as _encoder
    from email.header import make_header as _make_header
    from email.message import Message as _Message
    from email.mime.audio import MIMEAudio as _MIMEAudio
    from email.mime.base import MIMEBase as _MIMEBase
    from email.mime.image import MIMEImage as _MIMEImage
    from email.mime.multipart import MIMEMultipart as _MIMEMultipart
    from email.mime.text import MIMEText as _MIMEText
except:
    from email import Encoders as _encoder
    from email.Header import make_header as _make_header
    from email.MIMEMessage import Message as _Message
    from email.MIMEAudio import MIMEAudio as _MIMEAudio
    from email.MIMEBase import MIMEBase as _MIMEBase
    from email.MIMEImage import MIMEImage as _MIMEImage
    from email.MIMEMultipart import MIMEMultipart as _MIMEMultipart
    from email.MIMEText import MIMEText as _MIMEText
import mimetypes

class Message(object):
    ''' message binding for mail, such as recp,cc,subject,etc. '''
    def __init__(self, **kwargs):
        ''' init message with key,value arguments
        support
        - recp: list of recipient, required
        - cc: list of cc, optional
        - bcc: list of bcc, optional
        - subject: mail title, required
        - sender: optional, default as "user@hostname"
        - html: mail body of html
        - text: mail body of plain text
        - importance: "high" or "low"
        - attachments: file list
        e.g. Message(recp='foo@bar.com', subject='hello', text='world')
        '''
        self.sender = kwargs.get('sender') or self._get_default_sender()

        self.recp = kwargs.get('recp') or []
        self.cc = kwargs.get('cc') or []
        self.bcc = kwargs.get('bcc') or []

        self.subject = kwargs.get('subject') or u''
        self.html = kwargs.get('html') or u''
        self.text = kwargs.get('text') or u''

        self.importance = None
        if 'importance' in kwargs and kwargs['importance'] in ('high', 'low'):
            self.importance = kwargs['importance']

        self.encoding = kwargs.get('encoding') or 'utf-8'

        self._attachments = kwargs.get('attachments') or []
        return

    def get_receiver(self):
        ''' get all receivers '''
        return self.recp + self.cc + self.bcc

    def as_string(self):
        ''' encode email message as string '''
        msg = self._get_mine_message()
            
        # set message header
        msg['From'] = self._header(self.sender)
        msg['To'] = self._header(self.recp)
        msg['Subject'] = self._header(self.subject)
        if self.importance != None: msg['Importance'] = self.importance
        msg['Date'] = time.ctime()

        # attach message body
        if msg.is_multipart():
            # attach multiple parts if required
            part = _MIMEMultipart('alternative')
            self._attach_text(part, inline=True)
            self._attach_html(part, inline=True)
            msg.attach(part)

        # attach attachments
        self._attach_files(msg)
        return msg.as_string()

    def _get_default_sender(self):
        ''' generate default sender: "user@hostname" '''
        return '%s@%s' % (getpass.getuser(), socket.gethostname())

    def _header(self, value):
        ''' convert value to a valid mail header '''
        if isinstance(value, str):
            value = unicode(value, self.encoding)
        if isinstance(value, list) or isinstance(value, tuple):
            value = u'; '.join([unicode(i, self.encoding) for i in value])
        result = str(_make_header([(value, self.encoding)]))
        return result

    def _get_mine_message(self):
        ''' generate MIMEText or MIMEMultipart objects '''
        if self._attachments:
            return _MIMEMultipart('related')
        elif self.html:
            #return _MIMEMultipart('alternative')
            return _MIMEText(self.html, 'html', self.encoding)
        return _MIMEText(self.text, 'plain', self.encoding)

    def _attach_text(self, msg, inline=False):
        ''' attach plain text body '''
        part = _MIMEText(self.text, 'plain', self.encoding)
        if inline:
            part.add_header('Content-Disposition', 'inline')
        msg.attach(part)

    def _attach_html(self, msg, inline=False):
        ''' attach html body '''
        part = _MIMEText(self.html, 'html', self.encoding)
        if inline:
            part.add_header('Content-Disposition', 'inline')
        msg.attach(part)

    def _attach_files(self, outer):
        ''' attach file list '''
        for attachment in self._attachments:
            filename = attachment
            cid = None
            if (isinstance(attachment, list) or isinstance(attachment, tuple)
                    and len(attachment) == 2):
                filename, cid = attachment

            ctype, encoding = mimetypes.guess_type(filename)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            fp = open(filename, 'rb')
            if maintype == 'text':
                msg = _MIMEText(fp.read(), _subtype=subtype)
            elif maintype == 'image':
                msg = _MIMEImage(fp.read(), _subtype=subtype)
            elif maintype == 'audio':
                msg = _MIMEAudio(fp.read(), _subtype=subtype)
            else:
                msg = _MIMEBase(maintype, subtype)
                msg.set_payload(fp.read())
                _encoder.encode_base64(msg)
            fp.close()

            if cid:
                msg.add_header('Content-ID', '<%s>' % cid)
                msg.add_header('Content-Disposition', 'inline')
            else:
                msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(filename))
            outer.attach(msg)
        return


class Mailer(object):
    ''' python mailer module to send email '''
    def __init__(self, server='localhost'):
        ''' init with mail server, default as "localhost" to use /usr/sbin/sendmail(8) '''
        self._server = server
        self._smtp = smtplib.SMTP(self._server)
        self._user = None
        self._password = None

    def login(self, user, password):
        ''' login to send mail with smtp directly '''
        self._user = user
        self._password = password
        self._smtp.ehlo()
        self._smtp.starttls()
        self._smtp.ehlo()
        self._smtp.login(user, password)

    def send(self, msg):
        ''' send mail message '''
        me = msg.sender
        you = msg.get_receiver()
        self._smtp.sendmail(me, you, msg.as_string())
        self._smtp.quit()


def main():
    ''' main function
    '''
    msg = Message(recp = ['xiaoliang.zxl@taobao.com'],
            #sender = 'foobar@163.com',
            subject=u'hello from mailer module test',
            html=u'<html><body>hello world</body></html>',
            importance='low')
    mailer = Mailer()
    #mailer = Mailer('smtp.163.com')
    #mailer.login('foobar@163.com', 'password')
    mailer.send(msg)
    print 'Done'

if __name__ == '__main__':
    main()
