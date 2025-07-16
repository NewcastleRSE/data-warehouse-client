###############################################################################
# Manage a realistic set of test data for test data warehouse installation
###############################################################################

# Python modules
import argparse
import datetime
import inspect
import logging
import math
import random
import time

# User modules
from data_warehouse_client import data_warehouse

# Arguments
parser = argparse.ArgumentParser(
    prog = "PopulateDB"
)
parser.add_argument("credentials_file")
parser.add_argument("dbname")

logger = logging.getLogger(__name__)

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


def time_step(start, interval, mu=0, sigma=0, drift=(0,0)):
    """
    Generates a time based on previous time + an interval.
    The interval has a guassian distribution and duration drift
    start and interval should be in unix time.
    """
    # TODO: time interval should be absolute with a variance - this is
    # implemented such that there are actually two drifts, one Guassian
    # and one uniform distribution
    ts = start
    tint = interval
    def step():
        nonlocal ts, tint, mu, sigma, drift
        ts = ts + tint + random.gauss(mu, sigma)
        tint = tint * (1 + random.uniform(-drift[0], drift[1]))
        return ts
    return step


# Add elements
def add_studies(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    dw.add_study("Study One")
    dw.add_study("Test Data")

def add_trials(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Study One")[1]
    dw.insert_trial(study, "Baseline")
    dw.insert_trial(study, "6-month follow-up")
    dw.insert_trial(study, "12-month follow-up")

def add_measurement_groups(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Study One")[1]
    dw.add_measurement_group(study, "Test Group")
    study = dw.get_study("Test Data")[1]
    dw.add_measurement_group(study, "Q321")
    dw.add_measurement_group(study, "GFIT")
    dw.add_measurement_group(study, "Weather")

def add_units(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Test Data")[1]
    dw.add_unit(study, "Test Unit")
    dw.add_unit(study, "mg")
    dw.add_unit(study, "metres")
    dw.add_unit(study, "steps per minute")
    dw.add_unit(study, "Celsius")
    dw.add_unit(study, "%")

def add_measurement_types(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
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
    dw.add_measurement_type(study, 1, "Humidity", 5)
    dw.add_measurement_type(study, 7, "KCCQ clinical evaluation form, Item 10")

def add_categories(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Test Data")[1]
    dw.add_category(study, ["Y", "N"], 2)
    dw.add_category(study, ["Male", "Female", "Prefer not to say"], 4)
    dw.add_category(study, ["Y", "N"], 5)
    dw.add_category(study, ["Every Night", "3-4 times per week", "1-2 times per week", "Less than once per week", "Never over the past 2 weeks"], 9)

def add_boundsvals(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Test Data")[1]
    dw.add_boundsint(study, 16, 1, 6)
    dw.add_boundsreal(study, 13, 0.05, 3.5)
    dw.add_boundsdatetime(study, 8, datetime.datetime(2022, 1, 1), datetime.datetime(2122, 1, 1))

def link_mgts(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
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
    dw.connect_mt_to_mg(study, 14, 4, "TS01")
    dw.connect_mt_to_mg(study, 15, 4, "HS01")
    dw.connect_mt_to_mg(study, 16, 2, "C14.10")

def add_sourcetypes(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Test Data")[1]
    dw.insert_sourcetype(study, "Test Type")
    dw.insert_sourcetype(study, "q321", 1)
    dw.insert_sourcetype(study, "GFIT", 27)
    dw.insert_sourcetype(study, "Temperature Sensor", 12)
    dw.insert_sourcetype(study, "Humidity Sensor", 1)

def add_sources(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    dw.insert_source(2, "Test")
    dw.insert_source(2, "1")
    dw.insert_source(3, "1")
    dw.insert_source(4, "WS-34254")

def add_participants(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Test Data")[1]
    dw.insert_participant(study, "Test Participant")
    dw.insert_participant(study, "P123456")

def add_measurements(dw):
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Test Data")[1]
    values_1 = [(2, 4, 1), (3, 3, datetime.datetime.fromisoformat("1962-07-24")), (4, 5, 2), (5, 4, 0), (6, 2, "Parabennylzo Phetatine"), (7, 1, 2.50), (8, 3, "2012-09-07 06:10:00"), (9, 6, 3), (16, 7, 2)]
    values_2 = [(10, 1, 4.30), (11, 1, 1.03), (12, 1, 22.00), (13, 1, 5.30)]
    time_1 = datetime.datetime.fromisoformat("2020-03-08T14:05")
    time_2 = datetime.datetime.fromisoformat("2020-03-11T11:03")
    dw.insert_measurement_group(2, 2, values_1, time_1, None, 1, 1, None)
    dw.insert_measurement_group(2, 3, values_2, time_2, None, None, 2, None)

def add_synthetic_weather_measurements(dw, n):
    """
    15-minute sample simulation for 2 values. Time interval has a slight variation
    
    Reference:
        insert_measurement_group(self, study, measurement_group, values,
                                 time=-1, trial=None, participant=None, source=None, cursor=None):
    """
    logger.debug(inspect.currentframe().f_code.co_name)
    study = dw.get_study("Test Data")[1]
    vt = normal_float(15, 3, (-0.1, 0.1))
    vh = normal_float(70, 5)
    t = time_step(time.time(), 15*60, sigma=0.5)
    for step in range(n):
        dw.insert_measurement_group(study,
                                    4,
                                    [(14, 1, vt()), (15, 1, vh())],
                                    datetime.datetime.fromtimestamp(t()),
                                    None, None, 4, None)

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
#             |- datetimevalue
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

###############################################################################
# FK dependency tree
###############################################################################
# It would be better to build this from the database using SQL commands
# e.g. from https://stackoverflow.com/questions/1152260/how-to-list-table-foreign-keys
#
# SELECT conname, pg_catalog.pg_get_constraintdef(r.oid, true) as condef
# FROM pg_catalog.pg_constraint r
# WHERE r.confrelid = 'myschema.mytable'::regclass;
#
# or
#
# SELECT
#     tc.table_schema, 
#     tc.constraint_name, 
#     tc.table_name, 
#     kcu.column_name, 
#     ccu.table_schema AS foreign_table_schema,
#     ccu.table_name AS foreign_table_name,
#     ccu.column_name AS foreign_column_name 
# FROM information_schema.table_constraints AS tc 
# JOIN information_schema.key_column_usage AS kcu
#     ON tc.constraint_name = kcu.constraint_name
#     AND tc.table_schema = kcu.table_schema
# JOIN information_schema.constraint_column_usage AS ccu
#     ON ccu.constraint_name = tc.constraint_name
# WHERE tc.constraint_type = 'FOREIGN KEY'
#     AND tc.table_schema='myschema'
#     AND tc.table_name='mytable';
#
# TODO: Roll up the tables to be deleted in which order to avoid repeated
#       multiple deletions of the same tables. Although, it's not a slow process.

_fkdeptree = {
    "study" : (
        "boundsdatetime",
        "boundsint",
        "boundsreal",
        "category",
        "datetimevalue",
        "measurement",
        "measurementgroup",
        "measurementtype",
        "measurementtypetogroup",
        "participant",
        "source",
        "sourcetype",
        "textvalue",
        "trial",
        "units",
    ),
    "measurement" : (
        "textvalue",
        "datetimevalue",
    ),
    "measurementgroup" : (
        "measurement",
        "measurementtypetogroup",
    ),
    "measurementtype" : (
        "boundsdatetime",
        "boundsint",
        "boundsreal",
        "category",
        "measurement",
        "measurementtypetogroup",
    ),
    "participant" : (
        "measurement",
    ),
    "source" : (
        "measurement",
    ),
    "sourcetype" : (
        "source",
    ),
    "trial" : {
        "measurement",
    },
    "units" : (
        "measurementtype",
    )
}

_seqnames = {
        "measurement" : "Measurement_Id_seq",
        "measurementgroup" : "MeasurementGroup_Id_seq",
        "measurementtype" : "MeasurementType_Id_seq",
        "participant" : "Participant_Id_seq",
        "source" : "Source_Id_seq",
        "sourcetype" : "SourceType_Id_seq",
        "study" : "Study_Id_seq",
}

def reset_sequence(dw, table_name):
    """
    Reset a sequence back to the beginning and renumbers the table id column
    according to the sequence rules
    """
    logger.debug(inspect.currentframe().f_code.co_name)

    # TODO: make all of this more robust.
    #     - Get info out of PG for the given table
    #     - Don't cover up case-sensitivity of table and seuqnce names
    #q = """
    #    SELECT relkind FROM pg_class WHERE relname = '{}_Id_seq';
    #    """.format(table_name.title())
    #res = dw.return_query_result(q)
    #if not res:
    #    logger.debug("NO PRIMARY SEQUENCE")
    #    return

    if not table_name in _seqnames.keys():
        return

    logger.debug("RESETTING SEQUENCE: " + table_name)

    q = """
        ALTER SEQUENCE "{}" RESTART;
        UPDATE {} SET id = DEFAULT;
        """.format(_seqnames[table_name], table_name)
    cur = dw.dbConnection.cursor()
    try:
        cur.execute(q)
        dw.dbConnection.commit()
    except Exception as e:
        print(f"Error: {e}")
        dw.dbConnection.rollback()
        raise


def wipe_table(dw, table_name, rst=False):
    """
    Super destructive remove all data from a table recursively, with optional
    sequence reset
    """
    #logger.debug(inspect.currentframe().f_code.co_name + table_name)
    print("BEFORE", table_name)
    if table_name in _fkdeptree:
        for dep_table_name in _fkdeptree[table_name]:
            wipe_table(dw, dep_table_name, rst)
    print("AFTER", table_name, rst)
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

    if (rst):
        reset_sequence(dw, table_name)


def reset_data_warehouse(dw):
    """
    Completely reset a data warehouse, without dropping and creating the
    underlying table structure
    """
    #logger.debug(inspect.currentframe().f_code.co_name)
    wipe_table(dw, "study", True)
    pass


def build_data_warehouse(dw):
    #logger.debug(inspect.currentframe().f_code.co_name)
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
    add_synthetic_weather_measurements(dw, 100)

if __name__ == "__main__":
    """
    Main program for running all database setup actions
    """
    logging.basicConfig(level=logging.DEBUG)
    args = parser.parse_args()
    dw = data_warehouse.DataWarehouse(args.credentials_file, args.dbname)
    reset_data_warehouse(dw)
    build_data_warehouse(dw)
