###############################################################################
# Manage a realistic set of test data for test data warehouse installation
###############################################################################

# Python modules
import argparse
import datetime
import math
import random
import time

# User modules
from data_warehouse_client import data_warehouse

# Arguments

# Data generators
def normal_float(mu, sigma, drift=(0,0)):
    """
    Floating point generator with normal variation and mean drift
    """
    muv = mu
    def randomval():
        nonlocal muv, drift
        val = random.gauss(muv, sigma)
        diff = random.uniform(drift[0], drift[1])
        print(diff)
        muv = muv * (1 + diff)
        return val
    return randomval

def normal_float_varying(mu, sigma, step, fn=lambda t : 1):
    """
    Floating point generator with normal variation and a step-based
    function multiplier
    """
    muv = mu
    t = 0
    while True:
        val = random.gauss(muv, sigma) * fn(t)
        t += step
        yield val

# Example
def run_example():
    def myf(t):
        return math.sin(t/10)
    a = normal_float_varying(10, 0, 3, myf)
    while True:
        val = next(a)
        for i in range(2*(10+int(val))):
            print("*", end="")
        print("")
        time.sleep(0.1)


def time_interval(start, interval, mu=0, sigma=0, drift=(0,0)):
    """
    Generates a time based on previous time + an interval.
    The interval has a guassian ditricbution and duration drift
    start and interval should be in unix time.
    """
    time = start
    intv = interval
    def step():
        nonlocal start, interval, mu, sigma, drift
        val = start + interval + random.gauss(mu, sigma)
        intv = intv * (1 + random.uniform(-drift[0], drift[1]))
        return val
    return step()




# Add elements
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


###############################################################################
# Database management
###############################################################################
# FK dependencies:
# study \
#       |- units
#       |- trial
#       |- textvalue
#       |- sourcetype
#       |- source
#       |- participant
#       |- measurementtypetogroup
#       |- measurementtype
#       |- measurementgroup
#       |- measurement
#       |- datetimevalue
#       |- category
#       |- boundsreal
#       |- boundsint
#       |- boundsdatetime
#
# measurement \
#             |- textvalue
#
# sourcetype \
#            |- source
#
# source \
#        |- measurement
#
# measurementgroup \
#                  |- measurementtypetogroup
#                  |- measurement
#
# measurementtype \
#                 |- measurementtypetogroup
#                 |- measurement
#                 |- category
#                 |- boundsreal
#                 |- boundsint
#                 |- boundsdatetime
#
# units \
#       |- measurementtype
#
# participant \
#             |- measurement
#
# trial \
#       |- measurement
#
# measurement \
#             | datetimevalue

def reset_sequence(dw, table_name):
    """
    Reset a sequence back to the beginning and renumbers the table id column
    according to the sequence rules
    """
    q = """
        ALTER SEQUENCE "{}_Id_seq" RESTART;
        UPDATE {} SET id = DEFAULT;
        """.format(table_name.title(), str.lower(table_name))
    cur = dw.dbConnection.cursor()
    try:
        cur.execute(q)
        dw.dbConnection.commit()
    except Exception as e:
        print(f"Error: {e}")
        dw.dbConnection.rollback()
        raise

def wipe_table(dw, table_name):
    """
    Super destructive remove all data from a table
    """
    q = """
        DELETE FROM {};
        """.format(str.lower(table_name))
    cur = dw.dbConnection.cursor()
    try:
        cur.execute(q)
        dw.dbConnection.commit()
    except Exception as e:
        print(f"Error: {e}")
        dw.dbConnection.rollback()
        raise

def reset_units(dw):
    pass

def reset_study(dw):
    reset_sequence(dw, "study")
    pass

def reset_data_warehouse(dw):
    """
    Completely reset a data warehouse, without dropping and creating the
    underlying table structure
    """
    pass


if __name__ == "__main__":
    dw = data_warehouse.DataWarehouse(credentials_file, dbname)
    add_studies(dw)
    add_trials(dw)
    add_measurement_groups(dw)
    add_units(dw)
    add_measurement_types(dw)
    add_categories(dw)
    add_boundsvals(dw)
    link_mgts(dw)
    add_sourcetypes(dw)
    add_sources(dw)
    add_participants(dw)
    add_measurements(dw)
