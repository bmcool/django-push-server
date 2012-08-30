# -*- encoding: utf-8 -*-
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from gcm.models import Device as GCMModel
from apns.models import Device as APNSModel

class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'device_name', 'modified_date']
    search_fields = ('device_id', 'device_name')
    date_hierarchy = 'modified_date'
    actions = ['broadcast_message']
    
    def broadcast_message(self, request, queryset):
        message = request.POST.get('message', None)
        if message:
            for device in queryset:
                try:
                    device.send_message(message)
                    self.message_user(request, _("Success."))
                except:
                    self.message_user(request, _("Failed."))
                    self.message_user(request, _("The iOS message length can't over 220 characters (or over 36 chinese words)."))
        else:
            self.message_user(request, _("Please enter the broadcast message."))
    broadcast_message.short_description = _("Broadcast message to devices")
    
admin.site.register(GCMModel, DeviceAdmin)
admin.site.register(APNSModel, DeviceAdmin)