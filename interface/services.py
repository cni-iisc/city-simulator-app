"""
services.py: queries models to get required inputs to launch a task in the background.
- this scripts abstracts the functions specified in tasks.py
"""
import uuid
from io import StringIO
import datetime

import os
import pandas as pd
import geopandas as gpd
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from .tasks import send_mail, run_instantiate
from .helper import get_activation_url, convert
from .models import (UserRegisterToken, UserPasswordResetToken, cityInstantiation)
import json
from django.contrib import messages
import logging
log = logging.getLogger('interface_log')

def send_template_email(recipient, subject, html_message, context):
    # TODO: Enable this when the mail configurations are in place
    # return send_mail.delay(recipient, subject, html_message, context)
    return True

def send_activation_mail(request, user):
    to_email = user.email
    UserRegisterToken.objects.filter(user=user).delete()

    # TODO: check if it exsists
    user_token = UserRegisterToken.objects.create(
        user=user,
        token=uuid.uuid4())

    subject = f"Citysim: New Account Activation for {user}"
    html_message = f"""
    Dear  {user},

    To activate your citysim user account, click on the following link:
    """

    context = {
        'protocol': request.is_secure() and 'https' or 'http',
        'domain': get_current_site(request).domain,
        'url': get_activation_url(user_token.token, request.GET.get('origin', None)),
        'full_name': user.get_full_name(),
    }
    log.info(f'Account activation email was sent to {to_email}')
    send_template_email(to_email, subject, html_message, context)


def send_forgotten_password_email(request, user):
    to_email = user.email
    UserPasswordResetToken.objects.filter(user=user).delete()

    # TODO: check if it exsists
    user_token = UserPasswordResetToken.objects.create(
        user=user,
        token=uuid.uuid4())

    subject = f"citysim: New Account Activation for {user}"
    html_message = f"""
    Dear  {user},

    To reset the password for your citysim user account, click on the following link:
    """
    context = {
        'protocol': request.is_secure() and 'https' or 'http',
        'domain': get_current_site(request).domain,
        'url': reverse("user_password_reset", kwargs={"token": user_token.token}),
        'full_name': user.get_full_name()
    }

    log.info(f'Forgot password link email was sent to {to_email}')
    send_template_email(to_email, subject, html_message, context)

def instantiateTask(request):
    print("In instantiate_Task")
    user = request.user
    obj = cityInstantiation.get_latest(user=user) #gives id of the object
    obj = cityInstantiation.objects.filter(created_by=user, id=obj.id)[0]
    print(obj)
    print(obj.inst_name)

    inputFiles = {
        'demographics': pd.read_csv(StringIO(obj.inst_name.demographics_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'employment': pd.read_csv(StringIO(obj.inst_name.employment_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'households': pd.read_csv(StringIO(obj.inst_name.households_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'odmatrix': pd.read_csv(StringIO(obj.inst_name.odmatrix_csv.read().decode('utf-8')), delimiter=',').to_dict(),
        'city_profile': json.load(obj.inst_name.city_profile_json),
        'city' : gpd.read_file(obj.inst_name.city_geojson).to_json(),
        'objid': obj.id
    }
    print("inputFiles Loaded")
    # print(inputFiles)
    # inputFilePath = '/'.join(['cityData', f"{ datetime.datetime.today().strftime('%Y%m%d') }", instance.city_name.replace(' ', '_'), filename])
    cityInstantiation.objects.filter(created_by=user, id=obj.id).update(status='Running')
    try:
        print("Starting celeryInst")
        run_instantiate.apply_async(queue='instQueue', kwargs={'inputFiles': json.dumps(inputFiles)})
        print("SentCeleryInst")
        # run_instantiate(inputFiles)
        ####################
    except Exception as e:
        print("Error at run_instantiate")
        print(e)
    return True

