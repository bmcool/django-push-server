# -*- encoding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from gcm.api import send_gcm_message

class Device(models.Model):
    reg_id = models.TextField(verbose_name=_("RegID"), blank=False)
    
    device_id = models.CharField(max_length=50, verbose_name=_("Device ID"), unique=True)
    device_name = models.CharField(max_length=255, verbose_name=_("Device Name"), blank=True, null=True)
    app_name = models.CharField(max_length=255, verbose_name=_("APP Name"))
    
    creation_date = models.DateTimeField(verbose_name=_("Creation date"), auto_now_add=True)
    modified_date = models.DateTimeField(verbose_name=_("Modified date"), auto_now=True)
    is_test_device = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    

    def __unicode__(self):
        return self.device_id

    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        ordering = ['-modified_date']

    @property
    def is_registered(self):
        """
        Check if we can send message to this device
        """
        pass

    def send_message(self, msg):
        """
        Send message to current device
        """
        return send_gcm_message(api_key=settings.GCM_APIKEY, reg_id=self.reg_id, data={'msg': msg}, collapse_key="message")