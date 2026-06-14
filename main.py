# ---- block fileConfig calls from deps without crashing ----
import logging, logging.config

def _safe_fileConfig(*args, **kwargs):
    # If you already set up logging via dictConfig/basicConfig, do nothing.
    logging.getLogger("app").warning(
        "Ignoring logging.config.fileConfig call from a dependency; "
        "using existing logging configuration."
    )
    return None  # fileConfig normally returns None

# Patch both the attribute and the imported symbol users might have cached
import logging.config as _lc
_lc.fileConfig = _safe_fileConfig
logging.config.fileConfig = _safe_fileConfig

# Now apply YOUR logging (dictConfig or basicConfig)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "level": "DEBUG",
                             "formatter": "simple", "stream": "ext://sys.stdout"}},
    "loggers": {"app": {"level": "INFO", "handlers": ["console"], "propagate": False}},
    "root": {"level": "WARNING", "handlers": ["console"]},
}
logging.config.dictConfig(LOGGING_CONFIG)
logging.getLogger("app").info("logging initialized")


import random
import pandas as pd
import json
import os

import vectorpy.config
from vectorpy.__EventStructure import LapZonesValues, PsmReportStatus, hwVersion, LapRangesForEmail, Categories
from datetime import datetime, timedelta, time
from vectorpy.vectorious_api_handler import VectoriousApiHandler
from vector_data_generator.models_data_managers import InterventionDataManager, MedicationPlan

def get_implant_id_by_patient_id(patient_id):
    response = api_handler.get_all_patients().json()
    patients = response.get("patients", [])
    for patient in patients:
        if patient.get("id") == patient_id:
            return patient.get("implantId")
    return None  # If not found

def simul(api_handler, patientid, action, daysnum, daysago):
    implant=get_implant_id_by_patient_id(patientid)

    print(implant)
    if (action == "DEL"):
        delete_meas_of_implant_by_date(api_handler, implant, patientid, datetime.now() - timedelta(days=daysnum))
        print('delete ', patientid)
    if (action == "SH"):
        generate_test_lap(api_handler, implant, daysnum, daysnum-daysago+1, 17, 3)
        print(patientid,' CREATE still high')
    if (action == "VH"):
        generate_test_lap(api_handler, implant, daysnum, daysnum-daysago+1, 25, 3)
        print(patientid,' CREATE very high')
    if (action == "OP"):
        generate_test_lap(api_handler, implant, daysnum, daysnum-daysago + 1, 9, 3)
        print(patientid,' CREATE optimal')
    if (action == "LO"):
        generate_test_lap(api_handler, implant, daysnum, daysnum-daysago+1, 3, 3)
        print(patientid, ' CREATE low')
    if (action == "VL"):
        generate_test_lap(api_handler, implant, daysnum, daysnum-daysago+1, -1, 3)
        print(patientid, ' CREATE Very low')
    if (action == "RES"):
        api_handler.reset_patient(patientid)
        api_handler.delete_implant_statistics(implant)
        print(patientid, ' Reset')
    if (action == "GET"):
        print(api_handler.get_all_patient_interventions(patientid).json())
        print(patientid, ' Action report')
    if (action == "UP"):
        api_handler.update_intervention_time_by_id(daysnum, datetime.now() - timedelta(days=90))
        print(patientid, ' PSM date updated')
    if (action == "INTDEL"):
        api_handler.delete_all_intervention(patientid)
        print(patientid, ' Interventions deleted')
    return True

def um(api_handler, patientid):
    implant=api_handler.get_patient_implant(patientid).json()["implant"]["implantId"]
    print(implant)
    api_handler.create_event(30, datetime.now() - timedelta(days=10), implant_id=implant)
    api_handler.create_event(30, datetime.now() - timedelta(days=9), implant_id=implant)
    api_handler.create_event(30, datetime.now() - timedelta(days=8), implant_id=implant)
    api_handler.create_event(00, datetime.now() - timedelta(days=7), implant_id=implant)
    api_handler.create_event(0, datetime.now() - timedelta(days=5), implant_id=implant)
    api_handler.create_event(0, datetime.now() - timedelta(days=4), implant_id=implant)
    api_handler.create_event(10, datetime.now() - timedelta(days=3), implant_id=implant)
    api_handler.create_event(10, datetime.now() - timedelta(days=1), implant_id=implant)
    api_handler.create_event(10, datetime.now() - timedelta(days=0), implant_id=implant)
    print(patientid, ' UM ready')
    return True

def training(api_handler, daysnum):
    simul(api_handler, "GP-01-015", "RES", daysnum, 0)
    response = api_handler.get_all_patient_interventions('GE-03-002', latest=True).json()
    if datetime.strptime(response['interventions'][0]['creationTime'], '%Y-%m-%dT%H:%M:%S') > datetime.now() - timedelta(days=2):
        int1 = response['interventions'][0]['id']
        int1 = int(int1)
        simul(api_handler, 'GE-03-002', "UP", int1, 0)
    elif datetime.strptime(response['interventions'][0]['creationTime'], '%Y-%m-%dT%H:%M:%S') < datetime.now() - timedelta(days=85):
        int1 = response['interventions'][0]['id']
        int1 = int(int1)
        api_handler.update_intervention_time_by_id(int1, datetime.now() - timedelta(days=14))
    api_handler.remove_from_follow_up('GE-03-002')
    generate_ampm_lap(api_handler, 368, daysnum-1, daysnum, 9, 2)
    api_handler.report_on_taken_diuretics(patient_id="GE-03-002", psm_medication_id=4206, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    response = api_handler.get_all_patient_interventions('GE-03-003', latest=True).json()
    if datetime.strptime(response['interventions'][0]['creationTime'],'%Y-%m-%dT%H:%M:%S') > datetime.now() - timedelta(days=2):
        int1 = response['interventions'][0]['id']
        int1 = int(int1)
        simul(api_handler, 'GE-03-003', "UP", int1, 0)
    elif datetime.strptime(response['interventions'][0]['creationTime'],'%Y-%m-%dT%H:%M:%S') < datetime.now() - timedelta(days=85):
        int1 = response['interventions'][0]['id']
        int1 = int(int1)
        api_handler.update_intervention_time_by_id(int1, datetime.now() - timedelta(days=14))
    api_handler.remove_from_follow_up('GE-03-003')
    simul(api_handler, "GE-03-003", "DEL", 18, 0)
    api_handler.create_event(random.gauss(11, 1), datetime.now() - timedelta(days=18), implant_id=465)
    api_handler.create_event(random.gauss(12, 1), datetime.now() - timedelta(days=17), implant_id=465)
    api_handler.create_event(random.gauss(13, 1), datetime.now() - timedelta(days=16),implant_id=465)
    api_handler.create_event(random.gauss(14, 1), datetime.now() - timedelta(days=15), implant_id=465)
    api_handler.create_event(random.gauss(15, 1), datetime.now() - timedelta(days=14), implant_id=465)
    api_handler.create_event(random.gauss(16, 1), datetime.now() - timedelta(days=13), implant_id=465)
    api_handler.create_event(random.gauss(17, 1), datetime.now() - timedelta(days=12), implant_id=465)
    simul(api_handler, "GE-03-003", "SH", 11, 0)
    api_handler.report_on_taken_diuretics(patient_id="GE-03-003", psm_medication_id=4546, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    api_handler.report_on_taken_diuretics(patient_id="GE-03-003", psm_medication_id=4547, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    api_handler.trigger_lap_value_is_still_high_notification(patient_id="GE-03-003")
    # for GE-03-003 in very high use 4544 and 4545
    response = api_handler.get_all_patient_interventions('GP-01-001', latest=True).json()
    if datetime.strptime(response['interventions'][0]['creationTime'],'%Y-%m-%dT%H:%M:%S') > datetime.now() - timedelta(days=2):
        int1 = response['interventions'][0]['id']
        int1 = int(int1)
        simul(api_handler, 'GP-01-001', "UP", int1, 0)
    elif datetime.strptime(response['interventions'][0]['creationTime'],'%Y-%m-%dT%H:%M:%S') < datetime.now() - timedelta(days=85):
        int1 = response['interventions'][0]['id']
        int1 = int(int1)
        api_handler.update_intervention_time_by_id(int1, datetime.now() - timedelta(days=14))
    api_handler.remove_from_follow_up('GP-01-001')
    simul(api_handler, "GP-01-001", "LO", daysnum, 0)
    api_handler.report_on_taken_diuretics(patient_id="GP-01-001", psm_medication_id=4184, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    api_handler.report_on_taken_diuretics(patient_id="GP-01-001", psm_medication_id=4185, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    print('Clinic ready')
    return True

def giladprep(api_handler, daysnum):
    simul(api_handler, "AMED-01-01", "OP", daysnum, 0)
    simul(api_handler, "AMED-01-02", "SH", daysnum, 0)
    simul(api_handler, "AMED-01-03", "OP", daysnum, 0)
    simul(api_handler, "AMED-01-04", "OP", daysnum, 0)
    simul(api_handler, "DE-03-DEMO1", "OP", daysnum, 0)
    simul(api_handler, "ES-02-DEMO1", "LO", daysnum, 0)
    simul(api_handler, "GP-01-002", "LO", daysnum, 0)
    api_handler.report_on_taken_diuretics(patient_id="GP-01-002", psm_medication_id=4534, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    simul(api_handler, "GP-01-003", "LO", daysnum, 0)
    api_handler.report_on_taken_diuretics(patient_id="GP-01-003", psm_medication_id=3037, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    simul(api_handler, "GP-01-004", "OP", daysnum, 0)
    simul(api_handler, "GP-01-005", "OP", daysnum, 0)
    api_handler.report_on_taken_diuretics(patient_id="GP-01-005", psm_medication_id=4596, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    simul(api_handler, "GP-01-006", "LO", daysnum, 0)
    api_handler.report_on_taken_diuretics(patient_id="GP-01-006", psm_medication_id=4606, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    simul(api_handler, "GP-01-007", "OP", daysnum, 0)
    api_handler.report_on_taken_diuretics(patient_id="GP-01-007", psm_medication_id=3067, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    api_handler.report_on_taken_diuretics(patient_id="GP-01-007", psm_medication_id=3068, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day=datetime.now().strftime("%Y-%m-%d"))
    simul(api_handler, "GP-01-008", "OP", daysnum, 0)
    simul(api_handler, "GP-01-009", "OP", daysnum, 0)
    simul(api_handler, "GP-01-010", "OP", daysnum, 0)
    simul(api_handler, "GP-01-012", "VH", daysnum, 0)
    simul(api_handler, "GP-01-014", "LO", daysnum, 0)
    simul(api_handler, "GP-01-020", "LO", daysnum, 0)
    simul(api_handler, "GP-01-021", "LO", daysnum, 0)
    simul(api_handler, "GP-01-022", "VH", daysnum, 0)
    simul(api_handler, "GP-01-023", "VH", daysnum, 0)
    simul(api_handler, "GP-01-024", "VH", daysnum, 0)
    simul(api_handler, "GP-01-025", "VH", daysnum, 0)
    simul(api_handler, "GP-01-026", "VH", daysnum, 0)
    simul(api_handler, "GP-01-027", "OP", daysnum, 0)
    simul(api_handler, "GP-01-028", "LO", daysnum, 0)
    simul(api_handler, "GP-01-029", "VH", daysnum, 0)
    simul(api_handler, "GP-01-030", "VH", daysnum, 0)
    simul(api_handler, "GP-01-031", "LO", daysnum, 0)
    simul(api_handler, "GP-01-032", "VH", daysnum, 0)
    simul(api_handler, "GP-01-033", "VH", daysnum, 0)
    simul(api_handler, "GP-01-034", "SH", daysnum, 0)


    print('Gilad Clinic ready')
    return True

def prepare(api_handler, patientidfrom, patientidto, training):
    implant = api_handler.get_patient_implant(patientidto).json()["implant"]["implantId"]
    api_handler.reset_patient(patientidto)
    api_handler.delete_implant_statistics(implant)
    api_handler.update_patient(patient_id=patientidto, max_target_lap=14)
    psm_generator = InterventionDataManager(api_handler)
    zones, medications , frequencies, doses, pills, times_of_day, lap_values, creation_time = generate_med_plan_data(psm_generator, patientidfrom)
    interventionid=generate_psm_for_patient(psm_generator, patientidto,  zones, medications , frequencies, doses, pills, times_of_day, lap_values, creation_time)
    simul(api_handler, patientidto, "UP", interventionid, 0)
    if training == 1:
        simul(api_handler, patientidto, "OP", 10, 0)
    print('ready ', patientidfrom)
    return True

def prepareVH(api_handler, patientid):
    implant = api_handler.get_patient_implant(patientid).json()["implant"]["implantId"]
    simul(api_handler, patientid, "DEL", 3, 0)
    # api_handler.delete_patient_history(patientid)
    # api_handler.update_patient(psm_enable=True, patient_id=patientid)
    # api_handler.delete_lap_status(patientid)
    api_handler.create_event(30, datetime.now() - timedelta(days=2), implant_id=implant)
    api_handler.create_event(30, datetime.now() - timedelta(days=1), implant_id=implant)
    api_handler.create_event(30, datetime.now() - timedelta(days=0), implant_id=implant)
    print('ready ', patientid)
    return True

def backtotarget(api_handler, patientid):
    implant = api_handler.get_patient_implant(patientid).json()["implant"]["implantId"]
    api_handler.delete_patient_history(patientid)
    simul(api_handler, patientid, "DEL",3, 0)
    simul(api_handler, patientid, "OP", 3, 0)
    print('ready ', patientid)
    return True

def delete_meas_of_implant_by_date(api_handler: VectoriousApiHandler, implant_id, patient_id, start_date:datetime = None):
    print("Deleting measurements from %s" % str(start_date))
    meas = get_im_succ_meas(api_handler,implant_id, start_date)
    meas_id = get_meas_id(meas)
    delete_meas_of_implant_by_meas_id(api_handler,meas_id,patient_id)
    return True


def get_im_succ_meas(api_handler, implant_id, start_date:datetime = None):
    """
    :param implant_id, api_handler, start_day (optional):
    :return: df of implant id succesful measurements - first line is oldest, last is newest
    """
    print("getting succesful measurement of implant ID %d" %implant_id)
    data = {'opCode': 13}
    if start_date is not None:
        data = {'startDate': start_date}
    return pd.DataFrame(api_handler.get_measurements_by_implant_id(implant_id, data))


def generate_med_plan_data(psm_generator, patientidfrom):
    if  (patientidfrom == "ES-II-01-001"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Torsemide (Demadex )", "Spironolactone"], ["Torsemide (Demadex)", "Spironolactone"], ["Torsemide (Demadex)", "Spironolactone"], ["Torsemide (Demadex)", "Spironolactone"]]
        doses = [[20, 25], [15, 25], [10, 25], [7.5, 25]]
        frequencies = [["EveryDay", "EveryDay"],["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"]]
        pills = [[4, 1], [3, 1], [2, 1], [1.5, 1]]
        times_of_day = [["AM", "AM"], ["AM", "AM"], ["AM", "AM"], ["AM", "AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-01-005"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida", "Aldactone"], ["Furosemida", "Aldactone"], ["Furosemida", "Aldactone"], ["Aldactone"]]
        doses = [[40, 40, 37.5], [40, 25], [20, 25], [25]]
        frequencies = [["EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay"]]
        pills = [[1, 1, 1.5], [1, 1], [0.5, 1], [1]]
        times_of_day = [["AM", "PM", "AM"], ["AM", "AM"], ["AM", "AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-01-008"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida", "Eplerenona"], ["Furosemida", "Furosemida", "Eplerenona"], ["Furosemida", "Furosemida", "Eplerenona"], ["Furosemida", "Furosemida", "Eplerenona"]]
        doses = [[80, 40, 37.5], [60, 40, 25], [40, 40, 25], [40, 20, 12.5]]
        frequencies = [["EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay", "EveryDay"],["EveryDay", "EveryDay", "EveryDay"],["EveryDay", "EveryDay", "EveryDay"]]
        pills = [[2, 1, 1.5], [1.5, 1, 1], [1, 1, 1], [1, 0.5, 0.5]]
        times_of_day = [["AM", "PM", "PM"], ["AM", "PM", "PM"], ["AM", "PM", "PM"], ["AM", "PM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-02-001"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"]]
        doses = [[120, 80], [120, 80], [80, 40], [80, 40]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"]]
        pills = [[3, 2], [3, 2], [2, 1], [2, 1]]
        times_of_day = [["AM", "PM"], ["AM", "PM"], ["AM", "PM"], ["AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-02-002"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"],
                       ["Furosemida", "Furosemida"]]
        doses = [[120, 120], [120, 80], [80, 40], [80, 40]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"],
                       ["EveryDay", "EveryDay"]]
        pills = [[3, 3], [3, 2], [2, 1], [2, 1]]
        times_of_day = [["AM", "PM"], ["AM", "PM"], ["AM", "PM"], ["AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-02-004"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida"], ["Furosemida"], ["Furosemida"], ["Furosemida"]]
        doses = [[100], [60], [20], [20]]
        frequencies = [["EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[2.5], [1.5], [0.5], [0.5]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-02-006"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"],
                       ["Furosemida", "Furosemida"]]
        doses = [[80, 80], [80, 80], [60, 40], [40, 40]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"],
                       ["EveryDay", "EveryDay"]]
        pills = [[2, 2], [2, 2], [1.5, 1], [1, 1]]
        times_of_day = [["AM", "PM"], ["AM", "PM"], ["AM", "PM"], ["AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-02-007"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"],
                       ["Furosemida", "Furosemida"]]
        doses = [[80, 80], [80, 60], [60, 40], [60, 40]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"],
                       ["EveryDay", "EveryDay"]]
        pills = [[2, 2], [2, 1.5], [1.5, 1], [1.5, 1]]
        times_of_day = [["AM", "PM"], ["AM", "PM"], ["AM", "PM"], ["AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-02-008"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"],
                       ["Furosemida", "Furosemida"]]
        doses = [[120, 80], [80, 80], [80, 40], [40, 40]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"],
                       ["EveryDay", "EveryDay"]]
        pills = [[3, 2], [2, 2], [2, 1], [1, 1]]
        times_of_day = [["AM", "PM"], ["AM", "PM"], ["AM", "PM"], ["AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-05-001"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida", "Clortalidona", "Spironolactone"], ["Furosemida", "Furosemida", "Clortalidona", "Spironolactone"], ["Furosemida", "Furosemida", "Spironolactone"],
                       ["Furosemida", "Furosemida", "Spironolactone"]]
        doses = [[80, 40, 25, 25], [60, 40, 0, 25], [40, 20, 25], [40, 0, 0]]
        frequencies = [["EveryDay", "EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay", "EveryDay"],
                       ["EveryDay", "EveryDay", "EveryDay"]]
        pills = [[2, 1, 0.5, 1], [1.5, 1, 0, 1], [1, 0.5, 1], [1, 0, 0]]
        times_of_day = [["AM", "PM", "AM", "PM"], ["AM", "PM", "AM", "PM"], ["AM", "PM", "PM"], ["AM", "PM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-05-002"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida", "Eplerenona", "Eplerenona", "Clortalidona"], ["Furosemida", "Furosemida", "Eplerenona", "Eplerenona", "Clortalidona"], ["Furosemida", "Furosemida", "Eplerenona", "Eplerenona"], ["Furosemida", "Furosemida", "Eplerenona", "Eplerenona"]]
        doses = [[100, 100, 25, 50, 50], [100, 80, 25, 50, 25], [80, 80, 25, 50], [60, 40, 25, 50]]
        frequencies = [["EveryDay", "EveryDay", "EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay", "EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay", "EveryDay", "EveryDay"]]
        pills = [[2.5, 2.5, 0.5, 1, 1], [2.5, 2, 0.5, 1, 0.5], [2, 2, 0.5, 1], [1.5, 1, 0.5, 1]]
        times_of_day = [["AM", "PM", "AM", "PM", "AM"], ["AM", "PM", "AM", "PM", "AM"], ["AM", "PM", "AM", "PM"], ["AM", "PM", "AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-II-05-003"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida", "Eplerenona", "Eplerenona", "Clortalidona"],
                       ["Furosemida", "Furosemida", "Eplerenona", "Eplerenona", "Clortalidona"], ["Furosemida", "Furosemida", "Eplerenona", "Eplerenona", "Clortalidona"],
                       ["Furosemida", "Furosemida", "Eplerenona", "Eplerenona"]]
        doses = [[120, 80, 25, 50, 50], [80, 60, 25, 50, 50], [80, 60, 25, 50, 25], [80, 40, 25, 25]]
        frequencies = [["EveryDay", "EveryDay", "EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay", "EveryDay", "EveryDay", "EveryDay"],
                       ["EveryDay", "EveryDay", "EveryDay", "EveryDay", "EveryDay"], ["EveryDay", "EveryDay", "EveryDay", "EveryDay"]]
        pills = [[3, 2, 1, 2, 1], [2, 1.5, 1, 2, 1], [2, 1.5, 1, 2, 0.5], [2, 1, 1, 1]]
        times_of_day = [["AM", "PM", "AM", "PM", "AM"], ["AM", "PM", "AM", "PM", "AM"], ["AM", "PM", "AM", "PM", "AM"], ["AM", "PM", "AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-03-002"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"], ["Furosemida", "Furosemida"],
                       ["Furosemida", "Furosemida"]]
        doses = [[80, 120], [80, 80], [40, 80], [40, 40]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"],
                       ["EveryDay", "EveryDay"]]
        pills = [[2, 3], [2, 2], [1, 2], [1, 1]]
        times_of_day = [["AM", "PM"], ["AM", "PM"], ["AM", "PM"], ["AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "DE-II-06-001"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Torasemid"], ["Torasemid"], ["Torasemid"], ["Torasemid"]]
        doses = [[15], [10], [5], [5]]
        frequencies = [["EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[1.5], [1], [0.5], [0.5]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "DE-04-003"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Torasemid", "Torasemid"], ["Torasemid"], ["Torasemid"], ["Torasemid"]]
        doses = [[10,10], [10], [5], [5]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[1,1], [1], [0.5], [0.5]]
        times_of_day = [["AM", "PM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "IL-II-02-001"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["פוסיד","פוסיד"], ["פוסיד","פוסיד"], ["פוסיד","פוסיד"], ["פוסיד","פוסיד"]]
        doses = [[120, 120], [120, 80], [80, 80], [40, 40]]
        frequencies = [["EveryDay","EveryDay"], ["EveryDay","EveryDay"], ["EveryDay","EveryDay"], ["EveryDay","EveryDay"]]
        pills = [[3,3], [3,2], [2,2], [1,1]]
        times_of_day = [["AM","PM"], ["AM","PM"], ["AM","PM"], ["AM","PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "IL-II-06-001"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["פוסיד"], ["פוסיד"], ["פוסיד"], ["פוסיד"]]
        doses = [[80], [60], [40], [20]]
        frequencies = [["EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[2], [1.5], [1], [0.5]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "IL-II-06-002"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["פוסיד"], ["פוסיד"], ["פוסיד"], ["פוסיד"]]
        doses = [[80], [60], [40], [20]]
        frequencies = [["EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[2], [1.5], [1], [0.5]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "GE-01-001"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Torsemide"], ["Torsemide"], ["Torsemide"], ["Torsemide"]]
        doses = [[20], [10], [5], [2.5]]
        frequencies = [["EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[4], [2], [1], [0.5]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "GE-01-002"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Torsemide"], ["Torsemide"], ["Torsemide"], ["Torsemide"]]
        doses = [[30], [20], [10], [5]]
        frequencies = [["EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[6], [4], [2], [1]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "GE-02-002"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["ტორასემიდი"], ["ტორასემიდი"], ["ტორასემიდი"], ["ტორასემიდი"]]
        doses = [[60], [50], [40], [20]]
        frequencies = [["EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[3], [2.5], [2], [1]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "GE-03-001"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["ვეროშპირონი", "ვეროშპირონი"], ["ვეროშპირონი"], ["ვეროშპირონი"], ["ვეროშპირონი"]]
        doses = [[50, 50], [50], [25], [12.5]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay"], ["EveryDay"], ["EveryDay"]]
        pills = [[2, 2], [2], [1], [0.5]]
        times_of_day = [["AM", "PM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "GE-03-002"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["ტორასემიდი"], ["ტორასემიდი"], ["ტორასემიდი"], ["ტორასემიდი"]]
        doses = [[20], [20], [20], [10]]
        frequencies = [["EveryDay"], ["EveryOtherDay"], ["ThreeTimesAWeek"], ["ThreeTimesAWeek"]]
        pills = [[1], [1], [1], [0.5]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "GE-03-003"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["ტორასემიდი"], ["ტორასემიდი"], ["ტორასემიდი"], ["ტორასემიდი"]]
        doses = [[40], [20], [20], [10]]
        frequencies = [["EveryDay"], ["EveryDay"], ["EveryOtherDay"], ["ThreeTimesAWeek"]]
        pills = [[2], [1], [1], [0.5]]
        times_of_day = [["AM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "ES-02-DEMO1"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemida", "Furosemida"],
                       ["Furosemida"], ["Furosemida"],
                       ["Furosemida"]]
        doses = [[160, 160], [160], [80], [40]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay"],
                       ["EveryDay"], ["EveryDay"]]
        pills = [[4, 4], [4], [2], [1]]
        times_of_day = [["AM", "PM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "DE-03-DEMO1"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Torasemid", "Torasemid"],
                       ["Torasemid"], ["Torasemid"],
                       ["Torasemid"]]
        doses = [[40, 40], [40], [20], [10]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay"],
                       ["EveryDay"], ["EveryDay"]]
        pills = [[4, 4], [4], [2], [1]]
        times_of_day = [["AM", "PM"], ["AM"], ["AM"], ["AM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    if (patientidfrom == "GP-01-010"):
        zones = ["VeryHigh", "High", "Optimal", "Low"]
        medications = [["Furosemide", "Furosemide"], ["Furosemide", "Furosemide"], ["Furosemide", "Furosemide"], ["Furosemide", "Furosemide"]]
        doses = [[120, 120], [80, 80], [40, 40], [20, 20]]
        frequencies = [["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"], ["EveryDay", "EveryDay"],
                       ["EveryDay", "EveryDay"]]
        pills = [[3, 3], [2, 2], [1, 1], [0.5, 0.5]]
        times_of_day = [["AM", "PM"], ["AM", "PM"], ["AM", "PM"], ["AM", "PM"]]
        lap_values = [20, 13, 9, 5]
        creation_time = datetime.now() - timedelta(days=7)
    return zones, medications , frequencies, doses, pills, times_of_day, lap_values, creation_time


def generate_psm_for_patient(psm_generator: InterventionDataManager, patientidto,zones, medications , frequencies, doses, pills, times_of_day, lap_values, creation_time):
    data = psm_generator.create_medication_plan_data(
           patient_id=patientidto,
           zones=zones,
           medications=medications,
           frequencies=frequencies,
           doses=doses,
           pills=pills,
           times_of_day=times_of_day,
           lap_values=lap_values,
           creation_time=creation_time
    )
    interventionid=psm_generator.create_intervention(patient_id=patientidto, created_by="Gilad the Shark", medication_plan=data)
    # interventionid=api_handler.create_intervention(patient_id=patientidto, medication_plan=data, different_instructions_for_each_zone=True, duplicate_instructions=True, more_than_one_instruction=True)
    return interventionid


def get_meas_id(meas_df):
    """
    :param meas_df:
    :param x:
    :return: meas_id as list
    """
    return meas_df.id.to_list()


def HCP_stage_connection(patient_id = "GE-02-001", implant_id = 457, api_handler = ''):
    # api_handler = VectoriousApiHandler("yovel@vectoriousmedtech.com", "Ya220595", "YACSBXON2L3TRAV2SPZSNXTVTL4745HN", implant_id=375, env="stage")
    psm_generator = InterventionDataManager(api_handler)
    # generate_psm_for_patient(psm_generator)
    # api_handler.get_all_patient_interventions(patient_id=patient_id).json()
    print(' ')
    # print('done')
    return api_handler


def delete_meas_of_implant_by_meas_id(api_handler, meas_id_list, patient_id):
    print("Deleting last %d measurements, LAP range and notifications" % len(meas_id_list))
    api_handler.delete_measurements_by_id(*meas_id_list)
    api_handler.delete_all_notification(patient_id)
    api_handler.delete_lap_status(patient_id)
    return True

def generate_test_lap(api_handler, implant_id, start_days = 60, amount = 30, mu = 10, sigma = 3):
    """
    start days is how many days in the past (0 is for today).
    amount is how many days to create from start days (1 is only for start date, 2 is for start date and the next day and so on. measurements are created with a day interval
    """

    for i in range(amount*2-1):
        api_handler.create_event(random.gauss(mu,sigma), datetime.now() + timedelta(days=-(start_days - i/2)), implant_id=implant_id)

def generate_ampm_lap(api_handler, implant_id, start_days = 60, amount = 30, mu = 10, sigma = 1):
    """
    start days is how many days in the past (0 is for today).
    amount is how many days to create from start days (1 is only for start date, 2 is for start date and the next day and so on. measurements are created with a day interval
    """

    for i in range(amount):
        morning_datetime = datetime.combine(datetime.today().date(), time(hour=8, minute=0))
        evening_datetime = datetime.combine(datetime.today().date(), time(hour=20, minute=0))
        api_handler.create_event(random.gauss(mu-2,sigma), morning_datetime + timedelta(days=-(start_days - i)), implant_id=implant_id)
        api_handler.create_event(random.gauss(mu+2, sigma), evening_datetime + timedelta(days=-(start_days - i)), implant_id=implant_id)
    return True

def json_to_excel():
    json_file = r'C:\Users\GiladPreminger\Vectorious Dropbox\Gilad Preminger\PC\Downloads\all_users.txt'
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Normalize JSON data to flatten nested structures
    df = pd.json_normalize(data['users'])

    # Save the DataFrame to an Excel file
    excel_file = r'C:\Users\GiladPreminger\Vectorious Dropbox\Gilad Preminger\PC\Downloads\all_users.xlsx'
    df.to_excel(excel_file, index=False)

def importpkl():
    # Load the pickle file
    df = pd.read_pickle(r'C:\VectoriousScripts\API-Testing-Staging\data.pkl')

    # Convert to DataFrame if necessary (skip this step if `df` is already a DataFrame)
    # df = pd.DataFrame(your_data)

    # Export to CSV
    df.to_csv(r'C:\VectoriousScripts\API-Testing-Staging\csvdata.csv', index=False)  # `index=False` if you don't want to include the index in your CSV
    return True

def checkfiles():
    directory = r'C:\VectoriousScripts\API-Testing-Staging'
    files = os.listdir(directory)
    print(files)
    return True

def act(api_handler):
    patients_data = api_handler.get_all_patients().json()
    patients_list = patients_data.get('patients', [])
    first = 1
    while True:
        while True:
            if first == 2:
                while True:
                    answer = input("\nDo you want to use the same patient?").strip().lower()
                    try:
                        if answer == "y" or answer == "n":
                            break
                        else:
                            print("Wrong value")
                    except ValueError:
                        print("Please enter a valid value")
                if answer == 'y':
                    first = 2
                    break
                else:
                    first = 1
            if first == 1:
                patientid = input("\nWhat is the patient ID on your phone?: ").strip().upper()
                matching_patient = next((patient for patient in patients_list if patient.get('id') == patientid), None)
                if matching_patient:
                    first = 2
                    break
                else:
                    print("Patient ID not found. Please check and try again.")

        while True:
            act1 = input("\nWhich action?\n1 - new measurements\n2 - delete measurements\n3 - Interventions list\n4 - Update intervention date\n5 - reset patient\n6 - prepare a patient\n7 - trigger High\n8 - trigger Target\n9 - hide patient\n10 - unhide patient\n11 - prepare AMEDs\n12 - AMED-01-05-6\n13 - trigger failure\n?")
            try:
                act1 = int(act1)
                if 1 <= act1 <=13:
                    break
                else:
                    print("Wrong choice")
            except ValueError:
                print("Please enter a number between 1 and 13.")

        if act1 == 1:
            while True:
                act2 = input("\nWhich LAP value? (mmHg): ").strip().upper()
                try:
                    act2 = int(act2)
                    if -10 <= act2 <= 50:
                        break
                    else:
                        print("Wrong value")
                except ValueError:
                    print("Please enter a valid value")
            dayssnum = input("\nFrom how many days (0 = today)?: ")
            daysago = input("\nUntil how many days ago (0 = today)?: ")
            dayssnum = int(dayssnum)
            daysago = int(daysago)
            implant = get_implant_id_by_patient_id(patientid)
            generate_test_lap(api_handler, implant, dayssnum, dayssnum - daysago + 1, act2, 3)
        elif (act1 == 2):
            while True:
                dayssnum = input("\nHow many days?: ")
                try:
                    dayssnum = int(dayssnum)
                    if 0 <= dayssnum <= 1000:
                        break
                    else:
                        print("Wrong value")
                except ValueError:
                    print("Please enter a valid value")
            simul(api_handler, patientid, "DEL", dayssnum, 0)
        elif (act1 == 3):
            simul(api_handler, patientid, "GET", 1, 0)
            response = api_handler.get_all_patient_interventions(patientid, latest=True).json()
            print(response)
            int1 = response['interventions'][0]['id']
            print(int1)
        elif (act1 == 4):
            response = api_handler.get_all_patient_interventions(patientid, latest=True).json()
            int1 = response['interventions'][0]['id']
            # int1 = input("What is the intervention id?: ")
            int1 = int(int1)
            simul(api_handler, patientid, "UP", int1, 0)
        elif (act1 == 5):
            simul(api_handler, patientid, "RES", 1, 0)
        elif (act1 == 6):
            simul(api_handler, patientid, "RES", 1, 0)
            input("Go to stage 210, enter a new PSM plan, and then click enter here: ")
            response = api_handler.get_all_patient_interventions(patientid, latest=True).json()
            int1 = response['interventions'][0]['id']
            int1 = int(int1)
            simul(api_handler, patientid, "UP", int1, 0)
            simul(api_handler, patientid, "OP", 3, 0)
            print('ready ', patientid)
        elif (act1 == 7):
            prepareVH(api_handler, patientid)
        elif (act1 == 8):
            implant = api_handler.get_patient_implant(patientid).json()["implant"]["implantId"]
            simul(api_handler, patientid, "DEL", 3, 0)
            api_handler.create_event(9, datetime.now() - timedelta(days=2), implant_id=implant)
            api_handler.create_event(9, datetime.now() - timedelta(days=1), implant_id=implant)
            api_handler.create_event(9, datetime.now() - timedelta(days=0), implant_id=implant)
            print('ready ', patientid)
        elif (act1 == 9):
            api_handler.update_patient(patientid, hidden_from=datetime.now())
        elif (act1 == 10):
            api_handler.clear_hidden_from(patientid)
        elif (act1 == 11):
            prepare(api_handler, 'GP-01-010', "AMED-01-01", 0)
            simul(api_handler,"AMED-01-01","OP",60, 0)
            simul(api_handler, "AMED-01-02", "DEL", 200,0)
            simul(api_handler, "AMED-01-02", "OP", 60, 15)
            api_handler.create_event(12, datetime.now() - timedelta(days=14), implant_id=1002)
            api_handler.create_event(15, datetime.now() - timedelta(days=13), implant_id=1002)
            api_handler.create_event(18, datetime.now() - timedelta(days=12), implant_id=1002)
            api_handler.create_event(22, datetime.now() - timedelta(days=11), implant_id=1002)
            api_handler.create_event(9, datetime.now() - timedelta(days=10), implant_id=1002)
            api_handler.create_event(7, datetime.now() - timedelta(days=9), implant_id=1002)
            api_handler.create_event(26, datetime.now() - timedelta(days=8), implant_id=1002)
            api_handler.create_event(29.4, datetime.now() - timedelta(days=7), implant_id=1002)
            api_handler.create_event(28.8, datetime.now() - timedelta(days=6), implant_id=1002)
            api_handler.create_event(7.2, datetime.now() - timedelta(days=5), implant_id=1002)
            api_handler.create_event(9.6, datetime.now() - timedelta(days=4), implant_id=1002)
            api_handler.create_event(19, datetime.now() - timedelta(days=3), implant_id=1002)
            api_handler.create_event(19, datetime.now() - timedelta(days=2), implant_id=1002)
            api_handler.create_event(20, datetime.now() - timedelta(days=1), implant_id=1002)
            api_handler.create_event(21, datetime.now() - timedelta(days=0), implant_id=1002)
            api_handler.delete_patient_history("AMED-01-02")
            api_handler.set_patient_lap_status("AMED-01-02", lap_status="Optimal", time_stamp=datetime.now() - timedelta(days=45))
            api_handler.set_patient_lap_status("AMED-01-02",lap_status="HighStep1", time_stamp=datetime.now() - timedelta(days=12))
            api_handler.set_patient_lap_status("AMED-01-02",lap_status="HighStep2", time_stamp=datetime.now() - timedelta(days=6))
            api_handler.set_patient_lap_status("AMED-01-02",lap_status="HighStep3", time_stamp=datetime.now() - timedelta(days=0))
            api_handler.update_task_time(task_id='LapExpiration/AMED-01-02-PATIENT', updated_time=datetime.now() + timedelta(days=3))
            api_handler.set_category(patient_id="AMED-01-02", category=Categories.priority)
            simul(api_handler, "AMED-01-03", "DEL", 200, 0)
            simul(api_handler, "AMED-01-03", "OP", 60, 15)
            simul(api_handler, "AMED-01-03", "SH", 14, 11)
            simul(api_handler, "AMED-01-03", "OP", 10, 0)
            api_handler.delete_patient_history("AMED-01-03")
            api_handler.set_patient_lap_status("AMED-01-03", lap_status="Optimal", time_stamp=datetime.now() - timedelta(days=45))
            api_handler.set_patient_lap_status("AMED-01-03", lap_status="HighStep1", time_stamp=datetime.now() - timedelta(days=12))
            api_handler.set_patient_lap_status("AMED-01-03", lap_status="Optimal", time_stamp=datetime.now() - timedelta(days=8))
            api_handler.update_task_time(task_id='LapExpiration/AMED-01-03-PATIENT', updated_time=datetime.now() + timedelta(days=3))
            simul(api_handler, "AMED-01-04", "DEL", 200, 0)
            simul(api_handler, "AMED-01-04", "OP", 60, 30)
            simul(api_handler, "AMED-01-04", "LO", 29, 27)
            simul(api_handler, "AMED-01-04", "OP", 23, 15)
            simul(api_handler, "AMED-01-04", "SH", 14, 12)
            simul(api_handler, "AMED-01-04", "OP", 11, 0)
            api_handler.delete_patient_history("AMED-01-04")
            api_handler.set_patient_lap_status("AMED-01-04", lap_status="Optimal", time_stamp=datetime.now() - timedelta(days=45))
            api_handler.set_patient_lap_status("AMED-01-04", lap_status="Low", time_stamp=datetime.now() - timedelta(days=27))
            api_handler.set_patient_lap_status("AMED-01-04", lap_status="None", time_stamp=datetime.now() - timedelta(days=24))
            api_handler.set_patient_lap_status("AMED-01-04", lap_status="Optimal", time_stamp=datetime.now() - timedelta(days=21))
            api_handler.set_patient_lap_status("AMED-01-04", lap_status="HighStep1", time_stamp=datetime.now() - timedelta(days=13))
            api_handler.set_patient_lap_status("AMED-01-04", lap_status="Optimal", time_stamp=datetime.now() - timedelta(days=8))
            api_handler.update_task_time(task_id='LapExpiration/AMED-01-04-PATIENT', updated_time=datetime.now() + timedelta(days=5))
            diuretics_fill_auto("AMED-01-03", 9813, fromd= datetime.today().date()- timedelta(days=31), tod=datetime.today().date(), taken = 0)
            diuretics_fill_auto("AMED-01-04", 9819, fromd= datetime.today().date()- timedelta(days=31), tod=datetime.today().date(), taken = 1)
            simul(api_handler, "AMED-01-07", "RES", 1, 0)
        elif (act1 == 12):
            prepare(api_handler, 'GP-01-010', "AMED-01-05", 0)
            simul(api_handler, "AMED-01-05", "OP", 60, 0)
            simul(api_handler, "AMED-01-06", "DEL", 200, 0)
            simul(api_handler, "AMED-01-06", "OP", 60, 15)
            simul(api_handler, "AMED-01-06", "SH", 14, 5)
            simul(api_handler, "AMED-01-06", "OP", 4, 0)
            api_handler.delete_patient_history("AMED-01-06")
            api_handler.set_patient_lap_status("AMED-01-06", lap_status="Optimal", time_stamp=datetime.now() - timedelta(days=45))
            api_handler.set_patient_lap_status("AMED-01-06", lap_status="HighStep1", time_stamp=datetime.now() - timedelta(days=12))
            api_handler.set_patient_lap_status("AMED-01-06", lap_status="HighStep2", time_stamp=datetime.now() - timedelta(days=9))
            api_handler.set_patient_lap_status("AMED-01-06", lap_status="HighStep3", time_stamp=datetime.now() - timedelta(days=6))
            api_handler.set_patient_lap_status("AMED-01-06", lap_status="Optimal", time_stamp=datetime.now() - timedelta(days=3))
            # api_handler.update_task_time(task_id='LapExpiration/AMED-01-02-PATIENT', updated_time=datetime.now() + timedelta(days=3))
            # api_handler.set_category(patient_id="AMED-01-02", category=Categories.priority)
        elif (act1 == 13):
            while True:
                fail1 = input("\nWhich failure?\n1 - Invalid\n2 - Incorrect\n10 - Short press\n11 - Open belt\n12 - Battery low\n14 - Position\n22 - Belt connected\n23 - Over temp\n? ")
                try:
                    fail1 = int(fail1)
                    if 1 <= fail1 <= 23:
                        break
                    else:
                        print("Wrong value")
                except ValueError:
                    print("Please enter a valid value")
            while True:
                belt1 = input("\nWhich belt?\n1 - 4.2\n2 - 5.6\n? ")
                try:
                    belt1 = int(belt1)
                    if 1 <= belt1 <= 2:
                        break
                    else:
                        print("Wrong value")
                except ValueError:
                    print("Please enter a valid value")
            implant1 = get_implant_id_by_patient_id(patientid)
            if (belt1 == 1):
                hw1 = hwVersion.hwVersion42
            else:
                hw1 = hwVersion.hwVersion56
            if (fail1 == 1):
                api_handler.trigger_invalid_measurements_notification(patient_id=patientid,mid_optimal_range=None,invalid_temp_ch=False,invalid_ref_ch=False,invalid_ic127_ch=False,invalid_real_ch=True, hw_version = hw1)
            elif (fail1 == 2):
                api_handler.create_event(-10, datetime.now() - timedelta(days=0), implant_id=implant1)
            else:
                api_handler.create_event(30, datetime.now() - timedelta(days=0), implant_id=implant1, opcode=fail1, hw_version = hw1)
        else:
            print("Wrong choice")
        while True:
            continue_prompt = input("\nDo you want to perform another action? (y/n): ").strip().lower()
            try:
                if continue_prompt == "y" or continue_prompt == "n":
                    break
                else:
                    print("Wrong value")
            except ValueError:
                print("Please enter a valid value")
        if continue_prompt != 'y':
            print("\nExiting the program. Goodbye!")
            break
    return

def diuretics_fill_auto(patient_id, med, fromd, tod, taken):
    # Ensure fromd and tod are datetime.date objects
    if isinstance(fromd, str):
        fromd = datetime.strptime(fromd, '%Y-%m-%d').date()
    if isinstance(tod, str):
        tod = datetime.strptime(tod, '%Y-%m-%d').date()

    current_date = fromd
    while current_date <= tod:
        days_since_start = (current_date - fromd).days

        report_day_str = current_date.isoformat()  # Convert date to ISO 8601 string

        if days_since_start % 17 == 0 and taken==1:
            # skip
            api_handler.report_on_taken_diuretics(
                patient_id=patient_id,
                psm_medication_id=med,
                taken=True,
                psm_report_status=PsmReportStatus.all_reported_at_least_one_skipped,
                report_day=report_day_str
            )
        elif days_since_start % 21 == 0 and taken==1:
            # not reported
            api_handler.report_on_taken_diuretics(
                patient_id=patient_id,
                psm_medication_id=med,
                taken=True,
                psm_report_status=PsmReportStatus.not_all_reported,
                report_day=report_day_str
            )
        else:
            api_handler.report_on_taken_diuretics(
                patient_id=patient_id,
                psm_medication_id=med,
                taken=True,
                psm_report_status=PsmReportStatus.all_taken,
                report_day=report_day_str
            )

        current_date += timedelta(days=1)

# HCP_stage_connection(patient_id = "GE-03-001", implant_id = 375, api_handler = api_handler)
api_handler = VectoriousApiHandler("giladp@vectoriousmedtech.com", "Kite459019@", "TCQGCNTS2AD35RWMCIB3LAOLH5AHF5BG", implant_id=375, env=vectorpy.config.Environments.stage)
print(' ')
# Demo patients daily measurement
# simul(api_handler,"DE-03-DEMO1", "OP",0)
# simul(api_handler,"ES-02-DEMO1", "OP",0)

# Reset demo patients
# prepare(api_handler,"DE-03-DEMO1", "DE-03-DEMO1")
# prepare(api_handler,"ES-02-DEMO1", "ES-02-DEMO1")

# Move demo patients to VH
# prepareVH(api_handler, "DE-03-DEMO1")
# prepareVH(api_handler, "ES-02-DEMO1")
# prepareVH(api_handler, "GE-03-002")
# backtotarget(api_handler, "GE-03-002")

# Prepare patient for training
# prepare(api_handler,"ES-II-01-001", "GP-01-009")
# prepare(api_handler,"ES-II-01-005", "GP-01-009")
# prepare(api_handler,"ES-II-01-008", "GP-01-009")
# prepare(api_handler,"ES-II-02-001", "GP-01-009")
# prepare(api_handler,"ES-II-02-002", "GP-01-009")
# prepare(api_handler,"ES-II-02-004", "GP-01-009")
# prepare(api_handler,"ES-II-02-006", "GP-01-009")
# prepare(api_handler,"ES-II-02-007", "GP-01-009")
# prepare(api_handler,"ES-II-02-008", "GP-01-009")
# prepare(api_handler,"ES-II-05-001", "GP-01-009")
# prepare(api_handler,"ES-II-05-002", "GP-01-009")
# prepare(api_handler,"ES-II-05-003", "GP-01-009")
# prepare(api_handler,"DE-II-06-001", "GP-01-009")

# act(api_handler)

# Move trained patient to very high
# prepareVH(api_handler, "GP-01-009")

# Daily procedure for trained clinic (jerarsi)
# training(api_handler, 1)

# Daily procedure for demo patients
# giladprep(api_handler, 0)

# api_handler.create_event(10, datetime.now(), implant_id=implant_id)
# api_handler.delete_all_measurements(implant_id)
# api_handler.update_intervention_time_by_id(26, datetime.now() - timedelta(days=90))
# api_handler.delete_all_intervention(patient_id)
# api_handler.delete_all_notification(patient_id)
# api_handler.delete_lap_status(patient_id)
# api_handler.delete_thresholds(patient_id)
# api_handler.delete_medication_plan(patient_id)
# generate_test_lap(api_handler,10,5)
# api_handler.get_all_patient_interventions(patient_id).json()
# api_handler.reset_patient("GE-03-001")
# api_handler.update_patient(patient_id='DE-06-003', patient_phone=str(random.randint(100000, 999999)))
# implant_id=api_handler.get_patient_implant("GP-01-001").json()["implant"]["implantId"]

# failed measurement
# api_handler.create_event(30, datetime.now() - timedelta(days=0), implant_id=507, opcode=13)
# api_handler.create_event(30, datetime.now() - timedelta(days=0), implant_id=720, opcode=10, hw_version = hwVersion.hwVersion56)
# Short press 10, Open belt 11, Battery low 12, Success 13, failure 14, Belt connected 22, Over temp 23

# invalid measurement
# api_handler.trigger_invalid_measurements_notification(patient_id="GP-01-020",mid_optimal_range=None,invalid_temp_ch=False,invalid_ref_ch=False,invalid_ic127_ch=False,invalid_real_ch=True,)
# api_handler.create_event(-10, datetime.now() - timedelta(days=0), implant_id=502)

# put patient in hidden:
# api_handler.update_patient('GP-01-003', hidden_from = datetime.now())

# remove patient from hidden:
# api_handler.clear_hidden_from('GP-01-020')



# diuretics_fill_auto("AMED-01-03", 9813, fromd= datetime.today().date()- timedelta(days=31), tod=datetime.today().date(), taken = 0)
# diuretics_fill_auto("AMED-01-04", 9819, fromd= datetime.today().date()- timedelta(days=31), tod=datetime.today().date(), taken = 1)

# api_handler.report_on_taken_diuretics(patient_id="GE-03-002", psm_medication_id=4206, taken=True, psm_report_status=PsmReportStatus.all_taken, report_day='2024-03-11')
# api_handler.report_on_taken_diuretics(patient_id="GE-03-002", psm_medication_id=4206, taken=True, psm_report_status=PsmReportStatus.all_reported_at_least_one_skipped, report_day='2025-05-27')
# api_handler.report_on_taken_diuretics(patient_id="GE-03-002", psm_medication_id=4206, taken=True, psm_report_status=PsmReportStatus.not_all_reported, report_day='2024-11-01')
# api_handler.store_low_questionnaire(patient_id="GP-01-001", did_take_medications="yes", fatigue_rate=5, dizziness_rate=5, thirstiness_rate=5, time_stamp=datetime.now())
# api_handler.update_a_medication("Furosemide (Lasix, Fusid)", "Furosemide")
# api_handler.create_a_medication("Potassium meq", "Potassium", "MEQ", 100)
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Metolazone", json={'newName': 'Metolazone ', 'type': 'Thiazide', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Metolazone ', 'hebrew': 'מטולאזון', 'georgian': 'მეტოლაზონი', 'italian': 'Metolazone', 'spanish': 'Metolazona', 'latinAmericanSpanish': 'Metolazona', 'russian': 'Метолазон', 'german': 'Metolazon', 'arabic': 'ميتولازون'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Furosemid", json={'newName': 'Furosemide', 'type': 'LoopDiuretic', 'doseUnit': 'MG', 'doseLimit': 400, 'usEnglish': 'Furosemide', 'hebrew': 'פוסיד', 'georgian': 'ფუროსემიდი', 'italian': 'Furosemide', 'spanish': 'Furosemida', 'latinAmericanSpanish': 'Furosemida', 'russian': 'Фуросемид', 'german': 'Furosemid', 'arabic': 'فوروسيميد'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Torsemide", json={'newName': 'Torsemide', 'type': 'LoopDiuretic', 'doseUnit': 'MG', 'doseLimit': 200, 'usEnglish': 'Torsemide ', 'hebrew': 'טורסמיד', 'georgian': 'ტორსემიდი', 'italian': 'Torsemide', 'spanish': 'Torasemida', 'latinAmericanSpanish': 'Torasemida', 'russian': 'Торсемид', 'german': 'Torasemid', 'arabic': 'تورسميد'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Triamterene (Dyrenium)", json={'newName': 'Triamterene', 'type': 'Potassium', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Triamterene', 'hebrew': 'טריאמטרן', 'georgian': 'ტრიამტერენი', 'italian': 'Triamterene', 'spanish': 'Triamtereno', 'latinAmericanSpanish': 'Triamtereno', 'russian': 'Триамтерен', 'german': 'Triamteren', 'arabic': 'تريامتيرين'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Eplerenone", json={'newName': 'Eplerenone ', 'type': 'Potassium', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Eplerenone ', 'hebrew': 'אפלרנון', 'georgian': 'ეპლერენონი', 'italian': 'Eplerenone', 'spanish': 'Eplerenona', 'latinAmericanSpanish': 'Eplerenona', 'russian': 'Эплеренон', 'german': 'Eplerenon', 'arabic': 'إبليرينون'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Bumetanide ", json={'newName': 'Bumetanide', 'type': 'LoopDiuretic', 'doseUnit': 'MG', 'doseLimit': 6, 'usEnglish': 'Bumetanide', 'hebrew': 'בומטניד', 'georgian': 'ბუმეტანიდი', 'italian': 'Bumetanide', 'spanish': 'Bumetanida', 'latinAmericanSpanish': 'Bumetanida', 'russian': 'Буметанид', 'german': 'Bumetanid', 'arabic': 'بوميتانيد'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Chlorothiazide", json={'newName': 'Chlorothiazide ', 'type': 'Thiazide', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Chlorothiazide ', 'hebrew': 'כלורותיאזיד', 'georgian': 'ქლოროთიაზიდი', 'italian': 'Clorotiazide', 'spanish': 'Clorotiazida', 'latinAmericanSpanish': 'Clorotiazida', 'russian': 'Хлоротиазид', 'german': 'Chlorothiazid', 'arabic': 'كلوروثيازيد'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Amiloride", json={'newName': 'Amiloride ', 'type': 'Potassium', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Amiloride ', 'hebrew': 'אמילוריד', 'georgian': 'ამილორიდი', 'italian': 'Amiloride', 'spanish': 'Amilorida', 'latinAmericanSpanish': 'Amilorida', 'russian': 'Амилорид', 'german': 'Amilorid', 'arabic': 'أميلورايد'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Hydrochlorothiazide", json={'newName': 'Hydrochlorothiazide ', 'type': 'Thiazide', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Hydrochlorothiazide ', 'hebrew': 'הידרוכלורותיאזיד', 'georgian': 'ჰიდროქლოროთიაზიდი', 'italian': 'Idroclorotiazide', 'spanish': 'Hidroclorotiazida', 'latinAmericanSpanish': 'Hidroclorotiazida', 'russian': 'Гидрохлоротиазид', 'german': 'Hydrochlorothiazid', 'arabic': 'هيدروكلوروثيازيد'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Indapamide", json={'newName': 'Indapamide ', 'type': 'Thiazide', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Indapamide ', 'hebrew': 'אינדפמיד', 'georgian': 'ინდაპამიდი', 'italian': 'Indapamide', 'spanish': 'Indapamida', 'latinAmericanSpanish': 'Indapamida', 'russian': 'Индапамид', 'german': 'Indapamid', 'arabic': 'إنداباميد'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/Hydrodiuril", json={'newName': 'Hydrochlorothiazide', 'type': 'Thiazide', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Hydrochlorothiazide', 'hebrew': 'הידרוכלורותיאזיד', 'georgian': 'ჰიდროქლოროთიაზიდი', 'italian': 'Idroclorotiazide', 'spanish': 'Hidroclorotiazida', 'latinAmericanSpanish': 'Hidroclorotiazida', 'russian': 'Гидрохлоротиазид', 'german': 'Hydrochlorothiazid', 'arabic': 'هيدروكلوروثيازيد'})
# api_handler.put(f"{api_handler.base_url}/{api_handler.tenant}/medications/nitrate", json={'newName': 'Isosorbide Mononitrate', 'type': 'Nitrate', 'doseUnit': 'MG', 'doseLimit': 100, 'usEnglish': 'Isosorbide Mononitrate', 'hebrew': 'איזוסורביד מונוניטראט', 'georgian': 'იზოსორბიდ მონონიტრატი', 'italian': 'Isosorbide Mononitrato', 'spanish': 'Mononitrato de isosorbida', 'latinAmericanSpanish': 'Mononitrato de isosorbida', 'russian': 'Изосорбид мононитрат', 'german': 'Isosorbiddinitrat', 'arabic': 'إيزوسوربيد أحادي النترات'})
# api_handler.get_all_medication().json()
# api_handler.delete_medication(medication_name)
# api_handler.delete_lap_status("GE-03-002")
# api_handler.delete_patient_history("GE-03-002")
# api_handler.update_patient(psm_enable=True, patient_id="GE-03-002")

# show the tasks scheduled to the patient - onboarding, no lap
# api_handler.get_tasks_by_patient_id('GP-01-020').json()
# update the time of the task - in these examples to a second from now (the scheduler works on GMT)
# api_handler.update_task_time(task_id='LapExpiration/GP-01-020-PATIENT', updated_time= datetime.now()-timedelta(minutes=179)-timedelta(seconds=59))
# api_handler.update_task_time(task_id='NoLapSequence/GP-01-020-PATIENT', updated_time= datetime.now()-timedelta(minutes=179)-timedelta(seconds=59))
# api_handler.update_task_time(task_id='onboardingAppSupport/GP-01-020-PATIENT', updated_time= datetime.now()-timedelta(minutes=179)-timedelta(seconds=59))
# api_handler.update_patient(patient_id = "GP-01-023", lap_status = "none", lap_status_modified_date = datetime.now()-timedelta(days=9), patient_status = "priority", patient_status_since = datetime.now()-timedelta(days=9))

# auto-py-to-exe
# pyinstaller --onefile main.py --paths=C:\Git\vectorpy --paths=C:\Git\vector-data-generator
# pull git

# json_to_excel()

# api_handler.trigger_lap_value_back_to_optimal_notification("GP-01-032")
# api_handler.trigger_low_lap_notification("GP-01-030")
# api_handler.trigger_lap_value_is_still_high_notification("GP-01-027")
# api_handler.trigger_very_high_lap_notification("GP-01-027")
# api_handler.trigger_lap_value_is_still_very_high_notification("GP-01-027")
# api_handler.trigger_lap_value_is_still_low_notification("GP-01-033")

# api_handler.get_all_patients().json()
# api_handler.get_patient_information('IL-II-05-001').json()
# api_handler.get_patient_mid_optimal_range('ES-II-02-001').json()
# api_handler.get_all_medication().json()
# api_handler.get_patient_threshold('GE-03-002', latest_flag = True).json()
# api_handler.get_patient_threshold('GE-03-002').json()
# api_handler.get_patient_psm('GE-03-002').json()
# api_handler.get_diuretics_compliance_map('ES-II-02-001',date(2023, 8, 2), date(2025, 3, 20)).json()
# get_patient_status_between_dates_by_telemetry(start_date: datetime, end_date: datetime, patient_id)
# api_handler.get_diuretics_adherence_report('ES-II-02-001',date(2023, 8, 2), date(2025, 3, 20)).json()
# api_handler.get_questionnaire_answers('ES-II-02-001').json()
# api_handler.get_all_sites().json()

# information about no lap, jump, and ranges - better than notifications
# api_handler.get_patient_history('GE-03-002').json()
# api_handler.get_patient_status_between_dates_by_patient_history(datetime(2023, 8, 2), datetime(2025, 3, 20),'IL-II-02-001')
# api_handler.get_patient_status_between_dates_by_telemetry(datetime(2023, 8, 2), datetime(2025, 3, 20),'IL-II-02-001')
# api_handler.get_all_patients().json()



# api_handler.store_high_questionnaire(patient_id='AMED-01-01',did_take_medications='yes',well_being_rate=5,breath_shortness_rate=5,swollen_ankle_rate=5)
# api_handler.set_patient_lap_status("AMED-01-01", lap_status ="HighStep2", time_stamp=datetime.now()-timedelta(days=0))
# api_handler.trigger_lap_value_high_step_effective_notification("AMED-01-02", LapRangesForEmail.high_step_2)