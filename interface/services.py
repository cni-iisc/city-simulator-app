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
from .tasks import send_mail, run_instantiate, run_simulation
from .helper import get_activation_url, convert
from .models import (UserRegisterToken, UserPasswordResetToken, cityInstantiation, simulationParams, simulationResults)
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



# def updateTransCoeff(cityId, BETA):
#     transmission_coefficients_json = json.loads(cityInstantiation.objects.get(id=cityId).trans_coeff_file)
#     for i in range(len(BETA)):
#         for e in transmission_coefficients_json:
#            if (e['type'] == BETA[i]['type']):
#                if e['beta'] != float(BETA[i]['beta']):
#                     e['beta'] = float(BETA[i]['beta']) #TODO: Add ALPHA parameter when it is available

#     cityInstantiation.objects.filter(id=cityId).update(
#         trans_coeff_file=json.dumps(
#             transmission_coefficients_json,
#             default=convert
#         )
#     )
#     return True

# # def addConfigJSON(obj, outPath):
# #     testing_capacity = int(obj.testing_capacity)

# #     # configJSON = configCreate(min_group_size, max_group_size, beta_scaling_factor, avg_num_assns, periodicity, minimum_hostel_time, testing_capacity)
# #     configJSON = configCreate
# #     f = open(f"{ outPath }/config.json", "w")
# #     f.write(json.dumps(configJSON))
# #     f.close()
# #     return True


def launchSimulationTask(request, cityID):#, cityId, BETA
    print("In Launch Simulation Task")
    user = request.user
    obj = simulationParams.get_latest(user=user) #gives id of the object
    obj = simulationParams.objects.filter(created_by=user, id=obj.id)[0]

    dirName = os.path.splitext(obj.city_instantiation.individuals_json.path)[0]
    dirName = dirName.rsplit('/', 1)[0]
    print(dirName)
    # dirName = './media/instantiation/20211210/TestforSimulation6'   #Testing simulation runs

    if not os.path.exists(dirName):
        print("Given input directory path does not exist")
        os.mkdir(dirName)
    
    print("Simulation Parameters Data Loaded")

    # updateTransCoeff(cityId, BETA)

    f = open(f"{ dirName }/{ obj.intervention.intv_name }.json", "w")
    f.write(json.dumps(json.loads(obj.intervention.intv_json)))
    f.close()


    # json.dump(json.loads(obj.city_instantiation.trans_coeff_file), open(f"{ dirName }/transmission_coefficients.json", 'w'), default=convert)
    # json.dump(obj.testing_protocol.testing_protocol_file, open(f"{ dirName }/testing_protocol.json", 'w'), default=convert)
    # addConfigJSON(obj, dirName)

    simulationParams.objects.filter(created_by=user, id=obj.id).update(status='Queued')
    print("All working until run_simulation called")
    res = run_simulation.apply_async(queue='simQueue', kwargs={'id': obj.id, 'dirName': dirName, 'intv_name': obj.intervention.intv_name})
    # res = run_simulation(obj.id, dirName, obj.enable_testing, obj.intervention.intv_name)
    # if res.get():
    #     messages.success(request, f"Simulation job name:  is complete")#{ obj.simulation_name }
    #     log.info(f"Simulation job name:  is complete")#{ obj.simulation_name }
    # else:
    #     messages.error(request, f"Simulation job name:  has failed. Please check the inputs used.")#{ obj.simulation_name }
    #     log.error(f"Simulation job name:  has failed.")#{ obj.simulation_name }