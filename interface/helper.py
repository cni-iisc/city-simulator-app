"""
helper.py: contains utility functions used in the application
"""
import os
import datetime
import numpy as np
import pandas as pd

from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .models import RegisterOrigin

## Function to check if an object is present in a model or not?
def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None

### Function to validate password
def validate_password(value):
    """Validates that a password is as least 6 characters long and has at least
    1 digit and 1 letter.
    """

    min_length = 6

    if len(value) <= min_length:
        raise ValidationError(_('Password must be at least {0} characters '
                                'long.').format(min_length))

    # check for digit
    if not any(char.isdigit() for char in value):
        raise ValidationError(_('Password must contain at least 1 digit.'))

    # check for letter
    if not any(char.isalpha() for char in value):
        raise ValidationError(_('Password must contain at least 1 letter.'))

### Function to generate activation URL for new users (currently disabled)
def get_activation_url(token, origin_name=None):
    activation_url = reverse("user_activation", kwargs={'token': token})
    origin = RegisterOrigin.objects.filter(name=origin_name).first()

    if origin:
        return '{}?origin={}'.format(activation_url, origin.name)
    else:
        return activation_url

### Function to ensure numpy.dtypes are converted to scalars
def convert(o):
    if isinstance(o, np.generic): return o.item()
    raise TypeError

## Function to validate inputs to create simulation
def validateFormResponse(formData):
    for key in formData.keys():
        ## Transmission coefficients should always be between 0 -- 1
        if 'beta_' in key and key != 'beta_scale':
            if not((float(formData[key][0]) >= 0) or (float(formData[key][0]) <=1)):
                return False

    ## Simulation name should be atleast 2 characters long
    if len(formData['simulation_name'][0]) < 2:
        return False

    ## Num-days to be atleast 1
    if int(formData['num_days'][0]) < 1:
        return False

    min_grp_size = int(formData['min_grp_size'][0])
    max_grp_size = int(formData['max_grp_size'][0])
    avg_associations =int(formData['avg_associations'][0])

    if (min_grp_size <= 0) or (min_grp_size >= max_grp_size):
        return False
    if (max_grp_size <= 0) or (min_grp_size >= max_grp_size):
        return False
    # ## Average number of associates should be atleast 1 and less than 20
    if (avg_associations <= 0) or (avg_associations >= 20):
        return False
    if not((avg_associations > min_grp_size) or (avg_associations < max_grp_size)):
        return False

    ## periodicity == 7
    if int(formData['periodicity'][0]) != 7:
        return False
    return True
