"""
services.py: queries models to get required inputs to launch a task in the background.
- this scripts abstracts the functions specified in tasks.py
"""
import uuid
from io import StringIO

import os
import pandas as pd
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from .tasks import send_mail
from .helper import get_activation_url, convert
from .models import (UserRegisterToken, UserPasswordResetToken)
import json
# from simulator.staticInst.config import configCreate
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

