from __future__ import absolute_import
from .helper import  convert
from django.core.files import File
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from anymail.exceptions import AnymailError
from config.celery import app
from .models import cityInstantiation
from io import StringIO
import json
import pandas as pd
from django.utils import timezone
import sys
import os
from .models import *
import billiard as multiprocessing

## logging
import logging
log = logging.getLogger('celery_log')

# Custom modules taken from submodule
from simulator.staticInst.CityGen import *


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

####################
@app.task()
def run_instantiate(inputFiles):
    print("in run_instantiate")
    ####################
    #debugging the JSON object must be str, bytes or bytearray, not 'dict' error
    #################
    # inputFiles = json.dumps(inputFiles)
    inputFiles = json.loads(inputFiles)
    print("run_instantiate_json_loaded")
    
    inputFiles['demographics'] = pd.DataFrame.from_dict(inputFiles['demographics'])
    inputFiles['employment'] = pd.DataFrame.from_dict(inputFiles['employment'])
    inputFiles['households'] = pd.DataFrame.from_dict(inputFiles['households'])
    inputFiles['odmatrix'] = pd.DataFrame.from_dict(inputFiles['odmatrix'])
    print("RIfilesloaded")
    # try:
    # individuals, interactionSpace, transCoeff2 =  campus_parse(inputFiles)
    city = City(inputFiles)
    print("City generated")
    population = 100000
    city.generate(population)
    individuals, houses, workplaces, schools, wardCentreDistances, commonAreas, fractionPopulations = city.dump_files()
    print("Dumped instantiated files")
    # indF = StringIO(json.dumps(individuals, default=convert))
    # intF = StringIO(json.dumps(interactionSpace, default=convert))

    indF = StringIO(json.dumps(individuals, default=convert))
    houseF = StringIO(json.dumps(houses, default=convert))
    workplaceF = StringIO(json.dumps(workplaces, default=convert))
    schoolF = StringIO(json.dumps(schools, default=convert))
    wardCentreDistanceF = StringIO(json.dumps(wardCentreDistances, default=convert))
    commonAreaF = StringIO(json.dumps(commonAreas, default=convert))
    fractionPopulationF = StringIO(json.dumps(fractionPopulations, default=convert))
    
    # campusInstantiation.objects.filter(id=inputFiles['objid'])[0].agent_json.save('individuals.json', File(indF))
    # campusInstantiation.objects.filter(id=inputFiles['objid'])[0].interaction_spaces_json.save('interaction_spaces.json', File(intF))

    cityInstantiation.objects.filter(id=inputFiles['objid'])[0].individuals_json.save('individuals.json', File(indF))
    cityInstantiation.objects.filter(id=inputFiles['objid'])[0].houses_json.save('houses.json', File(houseF))
    cityInstantiation.objects.filter(id=inputFiles['objid'])[0].workplaces_json.save('workplaces.json', File(workplaceF))
    cityInstantiation.objects.filter(id=inputFiles['objid'])[0].schools_json.save('schools.json', File(schoolF))
    cityInstantiation.objects.filter(id=inputFiles['objid'])[0].ward_centre_distance_json.save('wardCentreDistance.json', File(wardCentreDistanceF))
    cityInstantiation.objects.filter(id=inputFiles['objid'])[0].common_area_json.save('commonArea.json', File(commonAreaF))
    cityInstantiation.objects.filter(id=inputFiles['objid'])[0].fraction_population_json.save('fractionPopulation.json', File(fractionPopulationF))

    print("objects saved")

    cityInstantiation.objects.filter(id=inputFiles['objid']).update(
        # trans_coeff_file = json.dumps(transCoeff, default=convert),
        status = 'Complete',
        created_on = timezone.now()
    )
    log.info(f"Instantiaion job {cityInstantiation.objects.filter(id=inputFiles['objid'])[0].inst_name.city_name} was completed successfully.")
    del individuals, houses, workplaces, schools, wardCentreDistances, commonAreas, fractionPopulations
    return True
    # except Exception as e:
    #     cityInstantiation.objects.filter(id=inputFiles['objid']).update(
    #         status = 'Error',
    #         created_on = timezone.now()
    #     )
    #     print(e)
    #     print("Issue with instantiation")
    #     log.error(f"Instantiaion job {cityInstantiation.objects.filter(id=inputFiles['objid'])[0].inst_name.city_name} terminated abruptly with error {e} at {sys.exc_info()}.")
    #     return False


def run_cmd(prgCall):
    print(prgCall)
    outName = prgCall[1]
    if not os.path.exists(outName):
        os.mkdir(outName)
    os.system(prgCall[0] + outName)

@app.task()
def run_simulation(id, dirName):#  , intv_name, enable_testing,
    print("In Runsimulation")
    obj = simulationParams.objects.filter(id=id)
    obj.update(status='Running')
    obj = obj[0]
    log.info(f"Simulation job is now running.")#{ obj.simulation_name } 
    cmd = f"./simulator/cpp-simulator/drive_simulator"

    # if(enable_testing):
    #     cmd += f" --ENABLE_TESTING  --testing_protocol_filename ./testing_protocol.json"

    cmd += f" --input_directory {dirName} --output_directory "

    list_of_sims = [(cmd , f"{ dirName }/simulationOutputs") for i in range(1)]#range(obj.simulation_iterations){obj.simulation_name.replace(' ', '_')}

    

    pool = multiprocessing.Pool(multiprocessing.cpu_count() - 1)
    r = pool.map_async(run_cmd, list_of_sims)

    r.wait()
    try:
        log.info(f" Running sims for are complete")#{obj.simulation_name } 
        simulationParams.objects.filter(id=id).update(
        output_directory=f"{ dirName }/simulationOutputs",#{obj.simulation_name.replace(' ', '_')}
        status='Complete',
        completed_at=timezone.now()
        )
        # run_aggregate_sims(id)
        # log.info(f"Simulation job { obj.simulation_name } is complete and the results are aggregated.")
        return True
    except Exception as e:
        simulationParams.objects.filter(id=id).update(
            status = 'Error',
            created_on = timezone.now()
        )
        log.error(f"Simulation job  terminated abruptly with error {e} at {sys.exc_info()}.")#{ obj.simulation_name }
        return False