from __future__ import absolute_import
from .helper import  convert
from django.core.files import File
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from anymail.exceptions import AnymailError
from config.celery import app
# from .models import simulationParams, campusInstantiation
from io import StringIO
import json
import pandas as pd
from django.utils import timezone
import sys
import os
import billiard as multiprocessing

## logging
import logging
log = logging.getLogger('celery_log')

## Custom modules taken from submodule
# from simulator.staticInst.campus_parse_and_instantiate import campus_parse
# from simulator.staticInst.default_betas import default_betas


@shared_task(bind=True, max_retries=settings.CELERY_TASK_MAX_RETRIES)
def send_mail(self, recipient, subject, html_message, context, **kwargs):
    # Subject and body can't be empty. Empty string or space return index out of range error
    message = EmailMultiAlternatives(
        subject=subject,
        body=html_message,
        from_email=settings.DJANGO_DEFAULT_FROM_EMAIL,
        to=[recipient]
    )
    message.attach_alternative(" ", "text/html")
    message.merge_data = {
        recipient: context,
    }
    try:
        message.send()
    except AnymailError as e:
        self.retry(e)
