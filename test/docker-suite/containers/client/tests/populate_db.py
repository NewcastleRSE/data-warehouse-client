import datetime

from data_warehouse_client import data_warehouse

def add_studies(dw):
    dw.add_study("Study One")
    dw.add_study("Test Data")

def add_trials(dw):
    study = dw.get_study("Study One")[1]
    dw.insert_trial(study, "Baseline")
    dw.insert_trial(study, "6-month follow-up")
    dw.insert_trial(study, "12-month follow-up")

def add_measurement_groups(dw):
    study = dw.get_study("Study One")[1]
    dw.add_measurement_group(study, "Test Group")
    study = dw.get_study("Test Data")[1]
    dw.add_measurement_group(study, "Q321")
    dw.add_measurement_group(study, "GFIT")
    dw.add_measurement_group(study, "Temperature Sensor")

def add_units(dw):
    study = dw.get_study("Test Data")[1]
    dw.add_unit(study, "Test Unit")
    dw.add_unit(study, "mg")
    dw.add_unit(study, "metres")
    dw.add_unit(study, "steps per minute")
    dw.add_unit(study, "Celsius")

def add_measurement_types(dw):
    study = dw.get_study("Study One")[1]
    dw.add_measurement_type(study, 4, "Test Type")
    study = dw.get_study("Test Data")[1]
    dw.add_measurement_type(study, 4, "Participant has read PIS")
    dw.add_measurement_type(study, 3, "Date of Birth")
    dw.add_measurement_type(study, 5, "Gender")
    dw.add_measurement_type(study, 4, "Comorbidity: PIT")
    dw.add_measurement_type(study, 2, "Name of Drug")
    dw.add_measurement_type(study, 1, "Dosage", 1)
    dw.add_measurement_type(study, 3, "Biopsy Date")
    dw.add_measurement_type(study, 6, "KCCQ clinical evaluation form, Item 5")
    dw.add_measurement_type(study, 1, "AWS", 2)
    dw.add_measurement_type(study, 1, "Distance", 2)
    dw.add_measurement_type(study, 1, "Stride Length", 2)
    dw.add_measurement_type(study, 1, "Cadence", 3)
    dw.add_measurement_type(study, 1, "Temperature", 4)
    dw.add_measurement_type(study, 7, "KCCQ clinical evaluation form, Item 10")

def add_categories(dw):
    study = dw.get_study("Test Data")[1]
    dw.add_category(study, ["Y", "N"], 2)
    dw.add_category(study, ["Male", "Female", "Prefer not to say"], 4)
    dw.add_category(study, ["Y", "N"], 5)
    dw.add_category(study, ["Every Night", "3-4 times per week", "1-2 times per week", "Less than once per week", "Never over the past 2 weeks"], 9)

def add_boundsvals(dw):
    study = dw.get_study("Test Data")[1]
    dw.add_boundsint(study, 15, 1, 6)
    dw.add_boundsreal(study, 13, 0.05, 3.5)
    dw.add_boundsdatetime(study, 8, datetime.datetime(2022, 1, 1), datetime.datetime(2122, 1, 1))

def link_mgts(dw):
    study = dw.get_study("Test Data")[1]
    dw.connect_mt_to_mg(study, 2, 2, "G1")
    dw.connect_mt_to_mg(study, 3, 2, "G3")
    dw.connect_mt_to_mg(study, 4, 2, "G5")
    dw.connect_mt_to_mg(study, 5, 2, "GC1")
    dw.connect_mt_to_mg(study, 6, 2, "C5")
    dw.connect_mt_to_mg(study, 7, 2, "C5.1")
    dw.connect_mt_to_mg(study, 8, 2, "X1")
    dw.connect_mt_to_mg(study, 9, 2, "C14.5")
    dw.connect_mt_to_mg(study, 10, 3, "WB1")
    dw.connect_mt_to_mg(study, 11, 3, "WB2")
    dw.connect_mt_to_mg(study, 12, 3, "WB3")
    dw.connect_mt_to_mg(study, 13, 3, "WB4")
    dw.connect_mt_to_mg(study, 14, 4, "TS1")
    dw.connect_mt_to_mg(study, 15, 2, "C14.10")

def add_sourcetypes(dw):
    study = dw.get_study("Test Data")[1]
    dw.insert_sourcetype(study, "Test Type")
    dw.insert_sourcetype(study, "q321", 1)
    dw.insert_sourcetype(study, "GFIT", 27)
    dw.insert_sourcetype(study, "Temperature Sensor", 12)

def add_sources(dw):
    dw.insert_source(2, "Test")
    dw.insert_source(2, 1)
    dw.insert_source(3, 1)
    dw.insert_source(4, 3267)

def add_participants(dw):
    study = dw.get_study("Test Data")[1]
    dw.insert_participant(study, "Test Participant")
    dw.insert_participant(study, "P123456")

def add_measurements(dw):
    study = dw.get_study("Test Data")[1]
    values_1 = [(2, 4, 1), (3, 3, datetime.datetime.fromisoformat("1962-07-24")), (4, 5, 2), (5, 4, 0), (6, 2, "Parabennylzo Phetatine"), (7, 1, 2.50), (8, 3, "2012-09-07 06:10:00"), (9, 6, 3), (15, 7, 2)]
    values_2 = [(10, 1, 4.30), (11, 1, 1.03), (12, 1, 22.00), (13, 1, 5.30)]
    values_3a = [(14, 1, 37.50)]
    values_3b = [(14, 1, 36.40)]
    values_3c = [(14, 1, 35.80)]
    time_1 = datetime.datetime.fromisoformat("2020-03-08T14:05")
    time_2 = datetime.datetime.fromisoformat("2020-03-11T11:03")
    time_3a = datetime.datetime.fromisoformat("2020-06-16T01:02")
    time_3b = datetime.datetime.fromisoformat("2020-05-11T13:03")
    time_3c = datetime.datetime.fromisoformat("2020-05-11T17:05")
    dw.insert_measurement_group(2, 2, values_1, time_1, None, 1, 1, None)
    dw.insert_measurement_group(2, 3, values_2, time_2, None, None, 2, None)
    dw.insert_measurement_group(2, 4, values_3a, time_3a, None, None, 3, None)
    dw.insert_measurement_group(2, 4, values_3b, time_3b, None, None, 3, None)
    dw.insert_measurement_group(2, 4, values_3c, time_3c, None, None, 3, None)

if __name__ == "__main__":
    dw = data_warehouse.DataWarehouse(credentials_file, dbname)
    add_studies(dw)
    add_trials(dw)
    add_measurementgroups(dw)
    add_units(dw)
    add_measurementtypes(dw)
    add_categories(dw)
    add_boundsvals(dw)
    link_mgts(dw)
    add_sourcetypes(dw)
    add_sources(dw)
    add_particpants(dw)
    add_measurements(dw)
