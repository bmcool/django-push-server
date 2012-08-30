"""
django-ios-push - Django Application for doing iOS Push Notifications
Originally written by Lee Packham (http://leenux.org.uk/ http://github.com/leepa)
Updated by Wojtek 'suda' Siudzinski <wojtek@appsome.co>

(c)2009 Lee Packham - ALL RIGHTS RESERVED
May not be used for commercial applications without prior concent.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from socket import socket

import datetime
import struct
import ssl
import binascii
import math

try:
    import json
except ImportError:
    import simplejson as json

class Device(models.Model):
    device_token = models.CharField(verbose_name=_("Device Token"), blank=False, max_length=64)
    
    device_id = models.CharField(max_length=50, verbose_name=_("Device ID"), unique=True)
    device_name = models.CharField(max_length=255, verbose_name=_("Device Name"), blank=True, null=True)
    app_name = models.CharField(max_length=255, verbose_name=_("APP Name"))
    
    creation_date = models.DateTimeField(verbose_name=_("Creation date"), auto_now_add=True)
    modified_date = models.DateTimeField(verbose_name=_("Modified date"), auto_now=True)
    is_test_device = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        ordering = ['-modified_date']

    def _getApnHostName(self):
        """
        Get the relevant hostname for the instance of the phone
        """
        if self.is_test_device:
            return settings.APN_SANDBOX_HOST
        else:
            return settings.APN_LIVE_HOST

    def _getApnCertPath(self):
        """
        Get the relevant certificate for the instance of the phone
        """
        if self.is_test_device:
            return settings.APN_SANDBOX_PUSH_CERT
        else:
            return settings.APN_LIVE_PUSH_CERT

    def send_message(self, alert, badge=0, sound="chime", content_available=False,
                        custom_params={}, action_loc_key=None, loc_key=None,
                        loc_args=[], passed_socket=None, custom_cert=None):
        """
        Send a message to an iPhone using the APN server, returns whether
        it was successful or not.

        alert - The message you want to send
        badge - Numeric badge number you wish to show, 0 will clear it
        sound - chime is shorter than default! Replace with None/"" for no sound
        content_available - newsstand notification about new content available
        sandbox - Are you sending to the sandbox or the live server
        custom_params - A dict of custom params you want to send
        action_loc_key - As per APN docs
        loc_key - As per APN docs
        loc_args - As per APN docs, make sure you use a list
        passed_socket - Rather than open/close a socket, use an already open one

        See http://developer.apple.com/iphone/library/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/ApplePushService/ApplePushService.html
        """
        aps_payload = {}

        alert_payload = alert
        if action_loc_key or loc_key or loc_args:
            alert_payload = {'body' : alert}
            if action_loc_key:
                alert_payload['action-loc-key'] = action_loc_key
            if loc_key:
                alert_payload['loc-key'] = loc_key
            if loc_args:
                alert_payload['loc-args'] = loc_args

        aps_payload['alert'] = alert_payload

        if badge:
            aps_payload['badge'] = badge

        if sound:
            aps_payload['sound'] = sound

        if content_available:
            aps_payload['content-available'] = 1

        payload = custom_params
        payload['aps'] = aps_payload

        # This ensures that we strip any whitespace to fit in the
        # 256 bytes
        s_payload = json.dumps(payload, separators=(',',':'))

        # Check we're not oversized
        if len(s_payload) > 256:
            raise OverflowError, 'The JSON generated is too big at %d - *** "%s" ***' % (len(s_payload), s_payload)

        fmt = "!cH32sH%ds" % len(s_payload)
        command = '\x00'
        msg = struct.pack(fmt, command, 32, binascii.unhexlify(self.device_token), len(s_payload), s_payload)

        if passed_socket:
            passed_socket.write(msg)
        else:
            s = socket()
            if custom_cert is None:
                custom_cert = self._getApnCertPath()
            c = ssl.wrap_socket(s,
                                ssl_version=ssl.PROTOCOL_SSLv3,
                                certfile=custom_cert)
            c.connect((self._getApnHostName(), 2195))
            c.write(msg)
            c.close()

        return True

    def __unicode__(self):
        return u"Device %s" % self.device_token

def sendMessageToPhoneGroup(devices_list, alert, badge=0, sound="chime", content_available=False,
                            custom_params={}, action_loc_key=None, loc_key=None,
                            loc_args=[], sandbox=False, custom_cert=None):
    """
    See the syntax for send_message, the only difference is this opens
    one socket to send them all.

    The caller must ensure that all phones are the same sandbox level
    otherwise it'll end up sending messages to the wrong service.
    """

    if sandbox:
        host_name = settings.APN_SANDBOX_HOST
    else:
        host_name = settings.APN_LIVE_HOST

    if custom_cert is None:
        if sandbox:
            custom_cert = settings.APN_SANDBOX_PUSH_CERT
        else:
            custom_cert = settings.APN_LIVE_PUSH_CERT

    chunkSize = 75
    currentChunk = 0

    while (currentChunk <= math.ceil(devices_list.count() / chunkSize)):
        s = socket()
        c = ssl.wrap_socket(s,
                            ssl_version=ssl.PROTOCOL_SSLv3,
                            certfile=custom_cert)
        c.connect((host_name, 2195))

        rangeMin = chunkSize * currentChunk
        rangeMax = rangeMin + chunkSize

        for device in devices_list[rangeMin:rangeMax]:
            device.send_message(alert, badge=badge, sound=sound, content_available=content_available, custom_params=custom_params,
                                action_loc_key=action_loc_key, loc_key=loc_key, loc_args=loc_args, passed_socket=c)

        c.close()
        currentChunk += 1

def doFeedbackLoop(sandbox = False):
    """
    Contact the APN server and ask for feedback on things that
    have not gone through so the iPhone list can be updated accordingly

    Does two things:
        1. Find all associated iPhone objects and set failed_device to True
        2. Return a dict of hexlified push IDs with the time_t

    Annoyingly, I've had to stub this out for now as it seems that sandbox
    feedback service just doesn't do anything at all!

    If Apple fix that, I can test/debug a lot easier. Until then...
    """
    raise NotImplementedError

    if sandbox:
        host_name = settings.APN_SANDBOX_FEEDBACK_HOST
        cert_path = settings.APN_SANDBOX_PUSH_CERT
    else:
        host_name = settings.APN_LIVE_FEEDBACK_HOST
        cert_path = settings.APN_LIVE_PUSH_CERT

    s = socket()
    c = ssl.wrap_socket(s,
                        ssl_version=ssl.PROTOCOL_SSLv3,
                        certfile=settings.APN_LIVE_PUSH_CERT)
    c.connect((settings.APN_FEEDBACK_HOST, 2196))

    full_buf = ''
    while 1:
        tmp = c.recv(38)
        print tmp
        if not tmp:
            break
        else:
            full_buf += tmp

    c.close()
