# -*- encoding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template
from apns.models import Device

@csrf_exempt
def device(request):
    """
    Register device

    Args:
        reg_id - reg id from android app
        device_id - unique device id
    """
    device_id = request.POST.get('device_id', None)
    if device_id:
        device, created = Device.objects.get_or_create(device_id=device_id)
        device.device_token = request.POST.get('device_token')
        device.device_name = request.POST.get('device_name')
        device.app_name = request.POST.get('app_name')
        device.save()
    
    return HttpResponse()
