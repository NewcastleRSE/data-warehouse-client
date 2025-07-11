# Copyright 2020 Newcastle University.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from sys import exit
import psycopg2
from json import load
from more_itertools import intersperse

from data_warehouse_client.file_utils import process_sql_template
from data_warehouse_client.transform_result_format import form_measurements, form_measurement_group
from data_warehouse_client.type_checks import check_int, check_real, check_datetime, valtypep


def get_participants_in_result(results):
    """
    find all participants in a set of results
    :param results: a list of measurements. Each measurement is held in a list with the following fields:
                    id,time,study,participant,measurementType,typeName,measurementGroup,
                    groupInstance,trial,valType,value
    :return: a list of unique participants from the measurements
    """
    participants = map(lambda r: r[3], results)  # pick out participant
    return list(set(participants))


def field_holding_value(val_type):
    """
    A helper function that returns the data warehouse field that holds measurement values of the type
    specified in the parameter
    :param val_type: the type of measurement
    :return: the database field holding the measurement value
    """
    val_types = {0: "measurement.valinteger", 1: "measurement.valreal", 2: "textvalue.textval",
                 3: "datetimevalue.datetimeval", 4: "measurement.valinteger", 5: "measurement.valinteger",
                 6: "measurement.valinteger", 7: "measurement.valinteger", 8: "measurement.valreal",
                 9: "datetimevalue.datetimeval", 10: "textvalue.textval"}
    try:
        return val_types[val_type]
    except KeyError:
        print("Error: valType out of range: ", val_type)
        return None


def mk_where_condition(first_condition, column, test, value):
    """
    :param first_condition: true if this is the first condition in a where clause
    :param column: column name in measurement table
    :param test: comparator for value
    :param value: value to be tested in the where clause
    :return: (where clause, first_condition)
    """
    if value != -1:
        condition = " WHERE " if first_condition else " AND "
        if column == "time":
            q = f'{condition} measurement.{column}{test}\'{str(value)}\''
        else:
            q = f'{condition} measurement.{column}{test}{str(value)}'
        first_condition = False
    else:
        q = ""
    return q, first_condition


def core_sql_from_for_measurements():
    """
    Creates the from clause used by many of the functions that query the data warehouse
    :return: the from clause used by several of the functions that query the data warehouse
    """
    return process_sql_template("core_sql_from_for_measurements.sql")


def core_sql_for_where_clauses(study: int, participant: int, measurement_type: int, measurement_group: int,
                               group_instance: int, trial: int, start_time, end_time):
    """
    Returns the where clauses used by many of the functions that query the data warehouse to filter out rows
    according to the criteria passed as parameters. A value of -1 for any parameter means that no filter is
    created for it
    :param study: a study id
    :param participant: a participant id
    :param measurement_type: a measurementType
    :param measurement_group: a measurementGroup
    :param group_instance: a groupInstance
    :param trial: a trial id
    :param start_time: the start of a time period of interest
    :param end_time: the end of a time period of interest
    :return: a tuple containing the SQL for the where clauses, and a boolean that is true if there are >0 clauses
    """
    first_condition = True
    (qs, first_condition) = mk_where_condition(first_condition, "study", "=", study)
    (qp, first_condition) = mk_where_condition(first_condition, "participant", "=", participant)
    (qmt, first_condition) = mk_where_condition(first_condition, "measurementtype", "=", measurement_type)
    (qmg, first_condition) = mk_where_condition(first_condition, "measurementgroup", "=", measurement_group)
    (qgi, first_condition) = mk_where_condition(first_condition, "groupinstance", "=", group_instance)
    (qst, first_condition) = mk_where_condition(first_condition, "trial", "=", trial)
    (qet, first_condition) = mk_where_condition(first_condition, "time", ">=", start_time)
    (qt, first_condition) = mk_where_condition(first_condition, "time", "<=", end_time)
    return f' {qs}{qp}{qmt}{qmg}{qgi}{qst}{qet}{qt} ', first_condition


def core_sql_for_where_clauses_for_cohort(study, participants, measurement_type: int,
                                          measurement_group: int, group_instance: int, trial: int, start_time,
                                          end_time):
    """
    Returns the where clauses used by functions that query the data warehouse to filter out rows
    according to the criteria passed as parameters. A value of -1 for any parameter means that no filter is
    created for it
    :param study: a study id
    :param participants: a list of participant ids
    :param measurement_type: a measurementType
    :param measurement_group: a measurementGroup
    :param group_instance: a groupInstance
    :param trial: a trial id
    :param start_time: the start of a time period of interest
    :param end_time: the end of a time period of interest
    :return: the SQL for the where clauses
    """
    participants_str = map(lambda p: str(p), participants)
    q = " WHERE measurement.participant IN (" + ' '.join(
        [elem for elem in intersperse(",", participants_str)]) + ") "
    first_condition = False
    (qs, first_condition) = mk_where_condition(first_condition, "study", "=", study)
    (qmt, first_condition) = mk_where_condition(first_condition, "measurementtype", "=", measurement_type)
    (qmg, first_condition) = mk_where_condition(first_condition, "measurementgroup", "=", measurement_group)
    (qgi, first_condition) = mk_where_condition(first_condition, "groupinstance", "=", group_instance)
    (qst, first_condition) = mk_where_condition(first_condition, "trial", "=", trial)
    (qet, first_condition) = mk_where_condition(first_condition, "time", ">=", start_time)
    (qt, first_condition) = mk_where_condition(first_condition, "time", "<=", end_time)
    return f' {q}{qs}{qmt}{qmg}{qgi}{qst}{qet}{qt} '


def make_value_test(val_type, value_test_condition):
    """
    creates a condition for the where clause of a query
    :param val_type: the type of the field being tested
    :param value_test_condition: the test of that field
    :return: a fragment of SQL that can be included in the where clause of a query
    """
    return f' ({field_holding_value(val_type)}{value_test_condition}) '


def core_sql_select_for_measurements():
    """
     Creates the select clause used by many of the functions that query the data warehouse
     :return: the select clause used by several of the functions that query the data warehouse
     """
    return process_sql_template("core_sql_select_for_measurements.sql")


def core_sql_for_measurements():
    """
    Creates the select and from clauses used by many of the functions that query the data warehouse
    :return: the select and from clauses used by several of the functions that query the data warehouse
    """
    return f'{core_sql_select_for_measurements()} {core_sql_from_for_measurements()}'


class DataWarehouse:
    def __init__(self, credentials_file, db_name):
        # construct a connection to the warehouse
        self.credentialsFile = credentials_file
        self.dbName = db_name
        # load credentials
        print("Loading credentials..")
        try:
            with open(self.credentialsFile, 'r') as fIn:
                creds = load(fIn)
        except Exception as e:
            exit("Unable to load the credential's file! Exiting.\n" + str(e))

        print("Connecting to the database..")
        # establish connection
        conn_string = f"dbname={self.dbName} user={creds['user']} host={creds['IP']} password={creds['pass']}"
        try:
            self.dbConnection = psycopg2.connect(conn_string)
        except Exception as e:
            exit("Unable to connect to the database! Exiting.\n" + str(e))
        print("Init successful! Running queries.\n")


    ###########################################################################
    # General SQL methods
    ###########################################################################
    def return_query_result(self, query_text):
        """
        executes an SQL query. It is used for SELECT queries.
        :param query_text: the SQL
        :return: the result as a list of rows.
        """
        cur = self.dbConnection.cursor()
        cur.execute(query_text)
        return cur.fetchall()


    def exec_insert_with_return(self, query_text):
        """
        Executes INSERT, commits the outcome and returns the result from the RETURNING clause.
        :param query_text: the SQL
        :return the result from the RETURNING clause
        """
        cur = self.dbConnection.cursor()
        cur.execute(query_text)
        self.dbConnection.commit()
        return cur.fetchone()


    def exec_sql_with_no_return(self, query_text):
        """
        executes SQL and commits the outcome. Used to execute INSERT, UPDATE and DELETE statements with no RETURNING.
        :param query_text: the SQL
        """
        cur = self.dbConnection.cursor()
        cur.execute(query_text)
        self.dbConnection.commit()


    ###########################################################################
    # Measurements methods
    ###########################################################################
    def get_measurements(self, study, participant=-1, measurement_type=-1, measurement_group=-1, group_instance=-1,
                         trial=-1, start_time=-1, end_time=-1):
        """
        This function returns all measurements in the data warehouse that meet the optional criteria specified
        in the keyword arguments.
        The result is a list of measurements. Each measurement is held in a list with the following fields:
            id,time,study,participant,measurementType,typeName,measurementGroup, groupInstance,trial,valType,value
        :param study: a study id
        :param participant: a participant id
        :param measurement_type: a measurementType
        :param measurement_group: a measurementGroup
        :param group_instance: a groupInstance
        :param trial: a trial id
        :param start_time: the start of a time period of interest
        :param end_time: the end of a time period of interest
        :return: a list of measurements. Each measurement is held in a list with the following fields:
            id,time,study,participant,measurementType,typeName,measurementGroup, groupInstance,trial,valType,value
        """
        (where_clause, first_condition) = core_sql_for_where_clauses(study, participant, measurement_type,
                                                                     measurement_group,
                                                                     group_instance, trial, start_time, end_time)
        mappings = {"core_sql": core_sql_for_measurements(), "where_clause": where_clause}
        query = process_sql_template("get_measurements.sql", mappings)
        raw_results = self.return_query_result(query)
        return form_measurements(raw_results)


    def aggregate_measurements(self, study, measurement_type, aggregation, participant=-1, measurement_group=-1,
                               group_instance=-1, trial=-1, start_time=-1, end_time=-1):
        """

        :param measurement_type: the type of the measurements to be aggregated
        :param study: a study id
        :param aggregation: the aggregation function: this can be any of the postgres SQL aggregation functions,
                                  e.g."avg", "count", "max", "min", "sum"
        :param participant: a participant id
        :param measurement_group: a measurementGroup
        :param group_instance: a groupInstance
        :param trial: a trial id
        :param start_time: the start of a time period of interest
        :param end_time: the end of a time period of interest
        :return: the result of the aggregation
        """
        mt_info = self.get_measurement_type_info(study, measurement_type)
        val_type = mt_info[0][2]
        (w, first_condition) = core_sql_for_where_clauses(study, participant, measurement_type, measurement_group,
                                                          group_instance, trial, start_time, end_time)
        q = f'SELECT {aggregation} ( {field_holding_value(val_type)} ) {core_sql_from_for_measurements()} {w}'
        raw_result = self.return_query_result(q)
        return raw_result[0][0]


    def get_measurements_with_value_test(self, study, measurement_type, value_test_condition, participant=-1,
                                         measurement_group=-1, group_instance=-1, trial=-1, start_time=-1, end_time=-1):
        """
        Find all measurement of a particular type whose value meets some criteria.
        :param measurement_type: the measurement type of the measurements to be tested
        :param study: a study id
        :param value_test_condition: a string holding the condition
                  against which the value in each measurement is compared.
        :param participant: a participant id
        :param measurement_group: a measurementGroup
        :param group_instance: a groupInstance
        :param trial: a trial id
        :param start_time: the start of a time period of interest
        :param end_time: the end of a time period of interest
        :return: a list of measurements. Each measurement is held in a list with the following fields:
            id,time,study,participant,measurementType,typeName,measurementGroup, groupInstance,trial,valType,value
        """
        (where_clause, first_condition) = core_sql_for_where_clauses(study, participant, measurement_type,
                                                                     measurement_group,
                                                                     group_instance, trial, start_time, end_time)
        mt_info = self.get_measurement_type_info(study, measurement_type)
        val_type = mt_info[0][2]  # find the value type of the measurement
        # Add a clause to test the field that is relevant to the type of the measurement
        condition = " WHERE " if first_condition else " AND "
        cond = make_value_test(val_type, value_test_condition)
        mappings = {"core_sql": core_sql_for_measurements(), "where_clause": where_clause, "condition": condition,
                    "cond": cond}
        query = process_sql_template("get_measurements_with_value.sql", mappings)
        raw_results = self.return_query_result(query)
        return form_measurements(raw_results)


    def get_measurements_by_cohort(self, study, cohort_id, participant=-1, measurement_type=-1,
                                   measurement_group=-1, group_instance=-1, trial=-1, start_time=-1, end_time=-1):
        """
        Find all measurements in a cohort that meet the criteria.
        :param cohort_id: the value of the category in measurementType 181 that represents the condition
        :param study: a study id
        :param participant: a participant id
        :param measurement_type: a measurement type id
        :param measurement_group: a measurement group id
        :param group_instance: a groupInstance
        :param trial: a trial id
        :param start_time: the start of a time period of interest
        :param end_time: the end of a time period of interest
        :return: a list of measurements. Each measurement is held in a list with the following fields:
            id,time,study,participant,measurementType,typeName,measurementGroup, groupInstance,trial,valType,value
        """
        (where_clause, first_condition) = core_sql_for_where_clauses(study, participant, measurement_type,
                                                                     measurement_group,
                                                                     group_instance, trial, start_time, end_time)
        condition = " WHERE " if first_condition else " AND "
        mappings = {"core_sql": core_sql_for_measurements(), "where_clause": where_clause, "condition": condition,
                    "cohort_id": str(cohort_id), "study": str(study)}
        query = process_sql_template("get_measurements_by_cohort.sql", mappings)
        raw_results = self.return_query_result(query)
        return form_measurements(raw_results)


    def mk_value_tests(self, value_test_conditions, study):
        """
        Helper function used to creat a Where clause to find measurements that fail the conditions
        :param value_test_conditions:   a list where each element is takes the following form:
                                        (measurementType,condition)
                                        where condition is a string holding the condition
                                        against which the value in each measurement is compared.
        :param study: study id
        :return:
        """
        all_conditions = []
        for (measurement_type, condition) in value_test_conditions:
            mt_info = self.get_measurement_type_info(study, measurement_type)
            val_type = mt_info[0][2]
            cond = f'((measurement.measurementtype = {str(measurement_type)}) AND NOT ' \
                   f'{make_value_test(val_type, condition)})'
            all_conditions = all_conditions + [cond]
        return ' '.join([elem for elem in intersperse(" OR ", all_conditions)])


    ###########################################################################
    # Measurement Type methods
    ###########################################################################
    def measurementtypep(self, id: int) -> bool:
        """
        measurementtype existence predicate
        :param: measurementtype id
        :return: True if id exists, False if not
        """
        q = " SELECT (id) FROM measurementtype WHERE measurementtype.id={}; ".format(id)
        res = self.return_query_result(q)
        return len(res)>0


    def num_types_in_a_measurement_group(self, study, measurement_group):
        """
        A helper function that returns the number of measurement types in a measurement group
        :param study: study id
        :param measurement_group: measurement group id
        :return: number of measurement types in the measurement group
        """
        mappings = {"measurement_group": str(measurement_group), "study": str(study)}
        query = process_sql_template("num_types_in_a_measurement_group.sql", mappings)
        num_types = self.return_query_result(query)
        return num_types[0][0]


    def get_types_in_a_measurement_group(self, study, measurement_group):
        """
        A helper function that returns the names of the measurement types in a measurement group
        :param study: study id
        :param measurement_group: measurement group id
        :return: list of names of the measurement types in the measurement group
        """
        mappings = {"measurement_group": str(measurement_group), "study": str(study)}
        query = process_sql_template("types_in_a_measurement_group.sql", mappings)
        type_names = self.return_query_result(query)
        return type_names


    def get_measurement_type_info(self, study, measurement_type_id):
        """
        Returns information on a measurement type
        :param study: the study id
        :param measurement_type_id: the id of a measurement type
        :return: a list containing the elements: id, description, value type, units name
        """
        mappings = {"measurement_type_id": str(measurement_type_id), "study": str(study)}
        query = process_sql_template("get_measurement_type_info.sql", mappings)
        return self.return_query_result(query)


    def mt_in_studyp(self, study: int, measurementtype: int):
        """
        Is measurement type in a study?
        :param measurementtype: measurementtype id
        :param study: study id
        :return: True | False
        """
        if not self.measurementtypep(study):
            return False
        q = """ SELECT COUNT(measurementtype.id) FROM measurementtype
                WHERE measurementtype.id={} AND measurementtype.study={};
            """.format(measurementtype, study)
        res = self.return_query_result(q)
        if res[0][0] > 0:
            return True
        else:
            return False


    def add_measurement_type(self, study: int, valtype: int, description: str, unit=None) -> int:
        """
        Adds a new measurementtype. A combination of the descriptive names and
        the value type should be unique within a study. If the combination
        already exists the function returns the id; otherwise it will create a
        new entry and return the id. If study, valtype or unit are not found, then
        the method returns (False, None)
        :param study: the study id
        :param valtype: the value type the measurement type represents
        :param description: the description of the measurement type
        :param unit (optional): the id of the unit attached to the measurementtype
        :return: (measurementtype added, measurementtype id)
        """
        # Reject non-present ids and value types
        if not (self.studyp(study) and valtypep(valtype)):
            return False, None
        if unit != None:
            if not self.unitp(unit):
                return False, None
        
        # Reject existing study, description and valtype combinations
        cur = self.dbConnection.cursor()
        q = """
            SELECT (id) FROM measurementtype
            WHERE study={} AND description='{}' AND valtype={};
            """.format(study, description, valtype)
        res = self.return_query_result(q)
        if len(res) > 0:
            return False, res[0][0]
        
        # Add the new measurementtype
        q = " SELECT MAX(id) FROM measurementtype; "
        res = self.return_query_result(q)  # find the biggest id
        max_id = res[0][0]
        if max_id is None:
            free_id = 0
        else:
            free_id = max_id + 1  # the next free id
        cur.execute("""
                    INSERT INTO measurementtype (id, description, valtype, units, study)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (free_id, description, valtype, unit, study))  # insert the new entry
        self.dbConnection.commit()
        return True, free_id

    
    ###########################################################################
    # Measurement Group methods
    ###########################################################################
    def get_measurement_group(self, study_id, description):
        """
        Maps from the measurement group description to the measurement group id used within the warehouse
        :param study_id: The study id
        :type study_id: int
        :param description: The description/name of the measurement group
        :type description: str
        :return: A tuple of two elements. The first element is True if the measurement group exists or False if
        otherwise. The second element is the id of the found measurement group.
        :rtype: tuple[bool, int]
        """

        q = " SELECT id FROM measurementgroup " \
            " WHERE measurementgroup.study       = " + str(study_id) + \
            " AND   measurementgroup.description = '" + description + "';"
        res = self.return_query_result(q)
        found = len(res) == 1
        if found:
            return found, res[0][0]
        else:
            # print("Event_type", measurementgroup_description, " not found in measurementgroup.description")
            return found, res


    def get_all_measurement_groups(self, study):
        """
        A helper function that returns information on all the measurement groups in a study
        :param study: the study id
        :return: a list of [measurement group id, measurement group description]
        """
        mappings = {"study": str(study)}
        query = process_sql_template("get_all_measurement_groups.sql", mappings)
        return self.return_query_result(query)


    def get_all_measurement_groups_and_types_in_a_study(self, study):
        """
        A helper function that returns information on all the measurement groups and types in a study
        :param study: the study id
        :return: a list of rows. Each row is a list whose elements are: measurement group id, measurement type id
                   and the name of the measurement type
        """
        # Return all measurement groups and measurement types in a study
        mappings = {"study": str(study)}
        query = process_sql_template("get_all_measurement_groups_and_types_in_a_study.sql", mappings)
        return self.return_query_result(query)


    def insert_measurement_group(self, study, measurement_group, values,
                                 time=-1, trial=None, participant=None, source=None, cursor=None):
        """
         Insert one measurement group
         :param study: the study id
         :param measurement_group: the measurement group
         :param values: a list of the values from the measurement group in the form (measurementType,valType,value)
         :param time: the time the measurement was taken. It defaults to the current time
         :param trial: optional trial id
         :param participant: optional participant id
         :param source: optional source
         :param cursor: database cursor
         :return success boolean, the measurement group instance, error message
         """
        if time == -1:  # use the current date and time if none is specified
            time = datetime.now()  # use the current date and time if none is specified

        group_instance = 0   # used temporarily for the first measurement inserted in the measurement group
        insert_error = False  # will be set to true if there is an error inserting any measurement in the group
        if cursor is None:     # no cursor has been passed into the function, so create one
            cur = self.dbConnection.cursor()
        else:
            cur = cursor
        for (measurement_type, val_type, value) in values:
            if val_type in [0, 4, 5, 6, 7]:  # the value must be stored in valInteger
                val_integer = value
                val_real = None
            elif val_type in [1, 8]:  # the value must be stored in valReal
                val_integer = None
                val_real = value
            elif val_type in [2, 3]:  # the value must be stored in the text or datetime tables
                val_integer = None
                val_real = None
            else:
                error_message = f'[Error in valType ({val_type}) in insert_measurement_group.' \
                                f'Study = {study}, Participant = {participant}, Trial = {trial}, ' \
                                f'Measurement Group = {measurement_group}, Measurement Type = {measurement_type},' \
                                f' value = {value}, Source = {source}]'
                val_integer = None
                val_real = None
                insert_error = True
                break   # Don't try to execute the insert if there's an error in the val_type
            if val_type == 4 and value not in [0, 1]:    # Error in boolean value
                error_message = f'[Error in boolean value in insert_measurement_group' \
                                f'Study = {study}, Participant = {participant}, Trial = {trial}, ' \
                                f'Measurement Group = {measurement_group}, Measurement Type = {measurement_type},' \
                                f' value = {value}, Source = {source}]'
                insert_error = True
                break    # Don't try to execute the insert if there's an error in the val_type
            try:
                cur.execute("""
                            INSERT INTO measurement (id,time,study,trial,measurementgroup,groupinstance,
                                                     measurementtype,participant,source,valtype,valinteger,valreal)
                            VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                            """,
                            (time, study, trial, measurement_group, group_instance, measurement_type, participant,
                             source, val_type, val_integer, val_real))
                gid = cur.fetchone()[0]   # get the id of the new entry in the measurement table
                if group_instance == 0:   # this is the first measurement in the group to be inserted
                    group_instance = gid  # set measurement group instance id to the id of the 1st measurement in group
                    # Now we know the id of the new measurement, set the groupinstance field to be the same value for
                    # all measurements in the group
                    cur.execute("""
                                UPDATE measurement SET groupinstance = %s
                                WHERE id = %s;
                                """,
                                (group_instance, group_instance))  # set the groupinstance for the first measurement
                if val_type == 2:  # it's a Text Value so make entry in textvalue table
                    cur.execute("""
                                INSERT INTO textvalue(measurement,textval,study)
                                VALUES (%s, %s, %s);
                                """,
                                (gid, value, study))
                if val_type == 3:  # it's a DateTime value so make entry in datetimevalue table
                    cur.execute("""
                                INSERT INTO datetimevalue(measurement,datetimeval,study)
                                VALUES (%s, %s, %s);
                                """,
                                (gid, value, study))
                error_message = ''
            except psycopg2.Error as e:   # an error has occurred when inserting into the warehouse
                error_message = f'[Error in insert_measurement_group. {e.pgcode} occurred: {e.pgerror}, ' \
                                f'Study = {study}, Participant = {participant}, Trial = {trial}, ' \
                                f'Measurement Group = {measurement_group}, Measurement Type = {measurement_type},' \
                                f' value = {value}, Source = {source}]'
                insert_error = True
                break  # ignore the remaining measurements to be inserted in teh measurement group
        success = not insert_error
        if success:     # no inserts in the measurement group raised an error
            self.dbConnection.commit()     # commit the whole measurement group insert
        else:
            self.dbConnection.rollback()   # rollback the whole measurement group insert
        if cursor is None:    # if the cursor was created in this function then close it
            cur.close()
        return success, group_instance, error_message


    def get_measurement_group_instances(self, study, measurement_group, value_test_conditions,
                                        participant=-1, trial=-1, start_time=-1, end_time=-1):
        """
        Return all instances of a measurement group in which one or more of the measurements within the
            instance meet some specified criteria
        :param measurement_group: a measurement group
        :param study: a study id
        :param value_test_conditions: a list where each element is takes the following form:
                                    (measurementType,condition)
                                       where condition is a string holding the condition
                                       against which the value in each measurement is compared.
        :param participant: a participant id
        :param trial: a trial id
        :param start_time: the start of a time period of interest
        :param end_time: the end of a time period of interest
        :return: a list of measurements. Each measurement is held in a list with the following fields:
                    id,time,study,participant,measurementType,typeName,measurementGroup,
                    groupInstance,trial,valType,value
        """
        problem_q = ""  # returns the instance ids of all instances that fail the criteria
        problem_q += " SELECT measurement.groupinstance "
        problem_q += core_sql_from_for_measurements()
        (w, first_condition) = core_sql_for_where_clauses(study, participant, -1, measurement_group, -1, trial,
                                                          start_time, end_time)
        problem_q += w
        if len(value_test_conditions) > 0:
            problem_q += " AND (" + self.mk_value_tests(value_test_conditions, study) + ")"

        outer_query = core_sql_for_measurements()
        outer_query += " " + w
        if len(value_test_conditions) > 0:
            outer_query += " AND measurement.groupinstance NOT IN (" + problem_q + ")"
        outer_query += " ORDER BY groupinstance, measurementtype"
        outer_query += ";"
        raw_results = self.return_query_result(outer_query)
        formed_measurements = form_measurements(raw_results)
        return form_measurement_group(self, study, measurement_group, formed_measurements)


    def get_measurement_group_instances_for_cohort(self, study, measurement_group, participants, value_test_conditions,
                                                   trial=-1, start_time=-1, end_time=-1):
        """
        Return all instances of a measurement group in which one or more of the measurements within the
            instance meet some specified criteria for the specified cohort of participants
        :param measurement_group: a measurement group
        :param study: a study id
        :param participants: a list of participant ids
        :param value_test_conditions: a list where each element is takes the following form:
                                    (measurementType,condition)
                                       where condition is a string holding the condition
                                       against which the value in each measurement is compared.
        :param trial: a trial id
        :param start_time: the start of a time period of interest
        :param end_time: the end of a time period of interest
        :return: a list of measurements. Each measurement is held in a list with the following fields:
                    id,time,study,participant,measurementType,typeName,measurementGroup,
                    groupInstance,trial,valType,value
        """
        problem_q = ""  # returns the instance ids of all instances that fail the criteria
        problem_q += " SELECT measurement.groupinstance "
        problem_q += core_sql_from_for_measurements()
        where_clause = core_sql_for_where_clauses_for_cohort(study, participants, -1, measurement_group,
                                                             -1, trial, start_time, end_time)
        problem_q += where_clause
        if len(value_test_conditions) > 0:
            problem_q += " AND (" + self.mk_value_tests(value_test_conditions, study) + ")"

        outer_query = core_sql_for_measurements()
        outer_query += where_clause
        if len(value_test_conditions) > 0:
            outer_query += " AND measurement.groupinstance NOT IN (" + problem_q + ")"
        outer_query += " ORDER BY groupinstance, measurementtype"
        outer_query += ";"
        raw_results = self.return_query_result(outer_query)
        formed_measurements = form_measurements(raw_results)
        return form_measurement_group(self, study, measurement_group, formed_measurements)


    def n_mg_instances(self, mg_id, study):
        """
        Return the number of instances of a measurement group in a study
        :param mg_id:
        :param study:
        :return: number of instances
        """
        q = " SELECT COUNT(DISTINCT measurement.groupinstance) FROM measurement "
        q += " WHERE measurement.study       = " + str(study)
        q += " AND measurement.measurementgroup = " + str(mg_id)
        q += " ;"
        res = self.return_query_result(q)
        return res[0][0]


    def mg_instances(self, mg_id, study):
        """
        Return the ids of instances of a measurement group in a study
        :param mg_id:
        :param study:
        :return: ids
        """
        q = " SELECT DISTINCT measurement.groupinstance FROM measurement "
        q += " WHERE measurement.study       = " + str(study)
        q += " AND measurement.measurementgroup = " + str(mg_id)
        q += " ORDER BY measurement.groupinstance;"
        res = self.return_query_result(q)
        return res
    
    
    def mg_in_studyp(self, study: int, measurementgroup: int):
        """
        Is a measurement group in a study?
        :param study: study id
        :param measurementgroup: measurementgroup id
        :return: True | False
        """
        q= """ SELECT COUNT(measurementgroup.id) FROM measurementgroup
               WHERE measurementgroup.id={} AND measurementgroup.study={};
           """.format(measurementgroup, study)
        res = self.return_query_result(q)
        if res[0][0] > 0:
            return True
        else:
            return False
        

    def get_type_ids_in_measurement_group(self, study, measurement_group):
        """
        A helper function that returns the ids of the measurement types in a measurement group
        :param study: study id
        :param measurement_group: measurement group id
        :return: list of ids of the measurement types in the measurement group
        """
        q = ""
        q += " SELECT "
        q += "    measurementtypetogroup.measurementtype  "
        q += " FROM "
        q += "    measurementtypetogroup "
        q += " WHERE "
        q += "    measurementtypetogroup.measurementgroup = "
        q += str(measurement_group)
        q += " AND "
        q += "    measurementtypetogroup.study = "
        q += str(study)
        q += " ORDER BY measurementtypetogroup.measurementtype"
        q += ";"
        type_ids = self.return_query_result(q)
        result = []
        for r in type_ids:
            result = result + [r[0]]
        return result
    

    def add_measurement_group(self, study_id, description):
        """
        Adds a new measurementgroup. Group names should be unique within a
        study. If the name already exists the function returns the id;
        otherwise it will create a new entry and return the id.
        :param study_id: The study id
        :type study_id: int
        :param description: The description/name of the measurement group
        :type description: str
        :return: A tuple of two elements. The first element is True if the measurement group exists after the execution
        of this function or False if otherwise. The second element is the id of the found measurement group.
        :rtype: tuple[bool, int]
        """
        if not self.studyp(study_id):
            return False, None

        inserted, id_mg = self.get_measurement_group(study_id=study_id, description=description)

        if not inserted:

            cur = self.dbConnection.cursor()

            retry = True
            while retry:
                try:
                    cur.execute(
                        """
                        INSERT INTO measurementgroup (id, description, study)
                        VALUES (DEFAULT, %s, %s);
                        """,
                        (description, study_id))  # insert the new entry
                    retry = False
                except psycopg2.errors.UniqueViolation:
                    self.dbConnection.rollback()
                    retry = True

            self.dbConnection.commit()

            inserted, id_mg = self.get_measurement_group(study_id=study_id, description=description)

        return inserted, id_mg
    
        
    def connect_mt_to_mg(self, study: int, mt: int, mg: int, name=None, optional=False) -> tuple:
        """
        """
        # Check that type and group exists in study
        if not (self.studyp(study) and
                self.mt_in_studyp(study, mt) and
                self.mg_in_studyp(study, mg)
                ):
            return False
        cur = self.dbConnection.cursor()
        cur.execute("""
                    INSERT INTO measurementtypetogroup (measurementtype, measurementgroup, name, study, optional)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (mt, mg,
                     ("NULL" if not name else name),
                     study,
                     ("false" if not optional else optional)))
        self.dbConnection.commit()
        return True


    ###########################################################################
    # Source methods
    ###########################################################################
    def get_sourcetype_by_description(self, description: str, study) -> tuple:
        """
        Gets the data warehouse entry for a description of a sourcetype
        :param description: the description
        :return: (id, description, version, study)
        """
        q = """
            SELECT id FROM sourcetype
            WHERE sourcetype.description='{}' and sourcetype.study = {};
            """.format(description, study)
        res = self.return_query_result(q)
        if len(res)>0:
            return True, res[0][0]
        else:
            return False, res


    def get_sourcetypes(self, study: int) -> tuple:
        """
        Get all sourcetypes in a study
        :param study_id: the study id
        :return: list of all the sourcetypes (id and sourcetype description)
        """
        q = """
            SELECT id, description FROM sourcetype
            WHERE sourcetype.study={};
            """.format(study)
        res = self.return_query_result(q)
        return res

    
    def sourcetypep(self, id: int) -> bool:
        """
        Sourcetype existence predicate
        :param: sourcetype id
        :return: True if id exists, False if not
        """
        q = " SELECT (id) FROM sourcetype WHERE sourcetype.id={}; ".format(id)
        res = self.return_query_result(q)
        return len(res)>0


    def add_sourcetype(self, study: int, description: str, version=None) -> tuple:
        """
        Adds a sourcetype
        :param study: the study that the sourcetype is attached to
        :param description: description string of the sourcetype
        :param version: (optional) version description
        :returns: id of the created entry, None on error (e.g. study does not exist)
        """
        # Ensure study id is valid
        if not self.studyp(study):
            return None
        cur = self.dbConnection.cursor()
        q = " SELECT MAX(id) FROM sourcetype; "
        res = self.return_query_result(q)  # find the biggest id
        max_id = res[0][0]
        if max_id is None:
            free_id = 0
        else:
            free_id = max_id + 1  # the next free id
        cur.execute("""
                    INSERT INTO sourcetype (id, study, description, version)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (free_id,
                     study,
                     description,
                     ("NULL" if not version else version)))  # insert the new entry
        self.dbConnection.commit()
        return free_id
    

    def update_sourcetype_version(self, id: int, version: str) -> tuple:
        """
        Updates a sourcetype version
        :param id: id of the sourcetype
        :param version: new version description
        :returns: id of the created entry, None on error (e.g. sourcetype does not exist)
        """
        if not (self.sourcetypep(id)):
            return None
        cur = self.dbConnection.cursor()
        cur.execute("""
                    UPDATE sourcetype
                    SET version=%s
                    WHERE id=%s;
                    """,
                    (version, id))
        self.dbConnection.commit()
        return id


    def get_source_by_description(self, description: str, sourcetype) -> tuple:
        """
        Gets a source entry corresponding to a description of a source
        :param description: the description
        :return: (id, description, sourcetype, study)
        """
        q = """
            SELECT id FROM source
            WHERE source.sourceid='{}' and source.sourcetype='{}';
            """.format(description, sourcetype)
        res = self.return_query_result(q)
        if len(res) > 0:
            return True, res[0][0]
        else:
            return False, res
        

    def add_source(self, sourcetype: int, sourceid: str) -> tuple:
        """
        Adds a source. This doesn't check for duplicate names.
        :param sourcetype: the sourcetype id that the source is an instance of
        :param sourceid: text description of the source (e.g. a serial number)
        :returns: id of the created entry, None on error (e.g. sourcetype does not exist)
        """
        # Find the study connected to the sourcetype
        q = """
            SELECT (study) FROM sourcetype
            WHERE sourcetype.id={};
            """.format(sourcetype)
        res = self.return_query_result(q)
        study = res[0][0]
        if study is None:
            return None
        
        # Get next free ID
        q = """
            SELECT MAX(id) FROM source;
            """
        res = self.return_query_result(q)
        max_id = res[0][0]
        if max_id is None:
            free_id = 0
        else:
            free_id = max_id + 1  # the next free id
        
        # Insert new entry
        cur = self.dbConnection.cursor()
        cur.execute("""
                    INSERT INTO source (id, sourceid, sourcetype, study)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (free_id,
                     sourceid,
                     sourcetype,
                     study))
        self.dbConnection.commit()
        return free_id
    

    ###########################################################################
    # Participant methods
    ###########################################################################
    def get_participant_by_id(self, study, participant):
        """
         maps from unique participant.id to the local id stored with measurements in the warehouse
         :param study: the study id
         :param participant: the id of the participant in the study
         :return The participantid of the participant
         """
        q = " SELECT participantid FROM participant " \
            " WHERE participant.study       = " + str(study) + \
            " AND participant.id = '" + str(participant) + "';"
        res = self.return_query_result(q)
        found = len(res) == 1
        if found:
            return found, res[0][0]
        else:
            # print("Participant", participant, " not found in participant.id")
            return found, res


    def get_participant(self, study_id, local_participant_id):
        """
        maps from a participantid that is local to the study, to the unique id stored with measurements in the warehouse
        :param study_id: the study id
        :param local_participant_id: the local participant id in the study
        :return The id of the participant
        """
        q = " SELECT id FROM participant " \
            " WHERE participant.study       = " + str(study_id) + \
            " AND participant.participantid = '" + local_participant_id + "';"
        res = self.return_query_result(q)
        found = len(res) == 1
        if found:
            return found, res[0][0]
        else:
            # print("Participant", local_participant_id, " not found in participant.participantid")
            return found, res


    def get_participants(self, study_id):
        """
        Get all participants in a study
        :param study_id: the study id
        :return: list of all the participants (id and participantid)
        """
        q = " SELECT id,participantid FROM participant " \
            " WHERE participant.study       = " + str(study_id) + ";"
        res = self.return_query_result(q)
        return res


    def add_participant(self, study_id, local_participant_id):
        """
        add a participant into the data warehouse
        :param study_id: the study id
        :param local_participant_id: the local name for the participant
        :res the new participant id
        """
        cur = self.dbConnection.cursor()
        q = " SELECT MAX(id) FROM participant " \
            " WHERE participant.study = " + str(study_id) + ";"
        res = self.return_query_result(q)  # find the biggest id
        max_id = res[0][0]
        if max_id is None:
            free_id = 0
        else:
            free_id = max_id + 1  # the next free id
        cur.execute("""
                    INSERT INTO participant(id,participantid,study)
                    VALUES (%s, %s, %s);
                    """,
                    (free_id, local_participant_id, study_id))  # insert the new entry
        self.dbConnection.commit()
        return free_id


    def add_participant_if_new(self, study_id, participant_id, local_participant_id):
        """
        add a participant into the data warehouse unless they already exist
        :param study_id: the study id
        :param participant_id: the participant_id
        :param local_participant_id: the local name for the participant
        :res (participant_added, new participant id)
        """
        cur = self.dbConnection.cursor()

        q = " SELECT id, participantid FROM participant " \
            " WHERE participant.study = " + str(study_id) + \
            " AND participant.id =  " + str(participant_id) + ";"
        res = self.return_query_result(q)
        participant_already_exists = len(res) > 0
        if participant_already_exists:
            return False, participant_id
        else:
            cur.execute("""
                        INSERT INTO participant(id,participantid,study)
                        VALUES (%s, %s, %s);
                        """,
                        (participant_id, local_participant_id, study_id))  # insert the new entry
            self.dbConnection.commit()
            return True, participant_id


    ###########################################################################
    # Study methods
    ###########################################################################
    def studyp(self, id: int) -> bool:
        """
        Study existence predicate
        :param: study id
        :return: True if id exists, False if not
        """
        q = " SELECT (id) FROM study WHERE study.id={}; ".format(id)
        res = self.return_query_result(q)
        return len(res)>0


    def get_studies(self) -> list:
        """
        Get all studies in the data warehouse
        :return: list of all the studies (id and studyid)
        """
        q = " SELECT (id, studyid) FROM study; "
        res = self.return_query_result(q)
        return res


    def get_study(self, local_study_id):
        """
        Gets the unique id of a study from a local study ID
        :param local_study_id: the local study id (researcher name for the study)
        :type local_study_id: str
        :return: A tuple of two elements. The first element is True if the study exists or False if otherwise. The
        second element is the id of the found study.
        :rtype: tuple[bool, int]
        """
        q = " SELECT id FROM study WHERE study.studyid ='{}'; ".format(local_study_id)

        res = self.return_query_result(q)
        n = len(res)
        found = n == 1
        if found:
            return found, res[0][0]
        elif n == 0:
            return found, res
        else:  # elif n > 1:
            raise ValueError('Multiple studies found with local study id "{}"'.format(local_study_id))


    def add_study(self, local_study_id):
        """
        Add a study into the data warehouse unless its label already exists
        :param local_study_id: researcher-defined label identifying the study
        :type local_study_id: str
        :return: A tuple of two elements. The first element is True if the study exists after the execution of this
        function or False if otherwise. The second element is the id of the study.
        :rtype: tuple[bool, int]
        """

        inserted, id_study = self.get_study(local_study_id)

        if not inserted:

            cur = self.dbConnection.cursor()

            retry = True
            while retry:
                try:
                    cur.execute(
                        """
                        INSERT INTO study (id, studyid)
                        VALUES (DEFAULT, %s);
                        """,
                        (local_study_id,))  # insert the new entry
                    retry = False
                except psycopg2.errors.UniqueViolation:
                    self.dbConnection.rollback()
                    retry = True

            self.dbConnection.commit()

            inserted, id_study = self.get_study(local_study_id)

        return inserted, id_study


    ###########################################################################
    # Trial methods
    ###########################################################################
    def get_trial_id_from_description(self, study, trial_description):
        """
         maps from the trial description to the trial id
         :param study: the study id
         :param trial_description: the description of the trial in the study
         :return a boolean to say if the description is found, and the trial id
         """
        q = " SELECT trial.id FROM trial " \
            " WHERE trial.study       = " + str(study) + \
            " AND trial.description = '" + trial_description + "';"
        res = self.return_query_result(q)
        found = len(res) == 1
        if found:
            return found, res[0][0]
        else:
            # print("Trial", trial_description, " not found in trial table")
            return found, res


    def get_trials_in_study(self, study: int) -> list:
        """
        Get all trials in the given study ID
        :return: list of all the trials (id, study, description)
        """
        q = " SELECT (id, study, description) FROM trial WHERE trial.study={} ; ".format(study)
        res = self.return_query_result(q)
        return res


    def add_trial(self, study: int, trial_description: str) -> int:
        """
        Add a trial into the data warehouse, for a particular study
        :param study: the study id to attach the trial to
        :param trial_description: a researcher-defined relevant string describing the trial
        :return the database id of the new trial
        """
        cur = self.dbConnection.cursor()
        q = " SELECT MAX(id) FROM trial; "
        res = self.return_query_result(q)  # find the biggest id
        max_id = res[0][0]
        if max_id is None:
            free_id = 0
        else:
            free_id = max_id + 1  # the next free id
        cur.execute("""
                    INSERT INTO trial (id, study, description)
                    VALUES (%s, %s, %s);
                    """,
                    (free_id, study, trial_description))  # insert the new entry
        self.dbConnection.commit()
        return free_id
    

    def add_trial_if_unique(self, study: int, trial_description: str) -> tuple:
        """
        Add a trial into the data warehouse unless its label already exists in the given study
        :param study: the study id to attach the trial to
        :param trial_description: a researcher-defined relevant string describing the trial
        :return (trial added, (id(s)))
        """
        cur = self.dbConnection.cursor()
        q = " SELECT (id) FROM trial WHERE description='{}' AND study={}; ".format(trial_description, study)
        res = self.return_query_result(q)
        trialyid_already_exists = len(res) > 0
        if trialyid_already_exists:
            return False, tuple([res[i][0] for i in range(len(res))])
        else:
            return True, (self.add_trial(study, trial_description),)
    

    ###########################################################################
    # Category methods
    ###########################################################################
    def get_category_id_from_name(self, study, measurement_type, category_name):
        """
        return the category id of a category
        :param study: the study id
        :param measurement_type: the measurement type
        :param category_name: the name of the category
        :return: exists?, category_id
        """
        q = " SELECT category.categoryid FROM category " \
            " WHERE  category.study       = " + str(study) + \
            " AND    category.measurementtype = " + str(measurement_type) + \
            " AND    category.categoryname = '" + category_name + "';"
        res = self.return_query_result(q)
        found = len(res) == 1
        if found:
            return found, res[0][0]
        else:
            return found, res


    def get_category_name_from_id(self, study, measurement_type, category_id):
        """
        return the category name of a category
        :param study: the study id
        :param measurement_type: the measurement type
        :param category_id: the id of the category
        :return: exists?, category_name
        """
        q = " SELECT category.categoryname FROM category " \
            " WHERE  category.study       = " + str(study) + \
            " AND    category.measurementtype = " + str(measurement_type) + \
            " AND    category.categoryid = " + str(category_id) + ";"
        res = self.return_query_result(q)
        found = len(res) == 1
        if found:
            return found, res[0][0]
        else:
            return found, res


    def add_category(self, study: int, cnames: list, measurementtype: int) -> int:
        """
        Adds a new measurement category. The organisation of the category data
        is up to the user. The category ids will be auto-generated in the order
        in which the category values are listed in cvalues. cnames should be
        in ascending order for ordinal data - it is assumed that the caller has
        taken care of this.
        :param study: the study id
        :param name: the name of the category
        :param cnames: the values in the category
        :param measurementtype: the measurementtype id
        :return: category added
        """
        # Reject invalid inputs
        if not (self.studyp(study) and
                (len(cnames) > 0)
                ):
            return (False, "Invalid parameter(s)")

        cur = self.dbConnection.cursor()

        # Check measurementtype is in the same study
        q= """ SELECT (id) FROM measurementtype
               WHERE measurementtype.id={} AND measurementtype.study={};
           """.format(measurementtype, study)
        res = self.return_query_result(q)
        if not (len(res) > 0):
            return (False, "measurementtype not found in study")

        # Check for empty ids in the cnames.
        # TODO: This should give more information or possibly raise an execption
        for cname in cnames:
            if not cname:
                return False

        # Reject existing study, description and valtype combinations
        for cid, cname in enumerate(cnames):
            cur.execute("""
                        INSERT INTO category (measurementtype, categoryid, categoryname, study)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (measurementtype, cid, cname, study))  # insert the new entry
        self.dbConnection.commit()
        return True
    

    ###########################################################################
    # Units methods
    ###########################################################################
    def unitp(self, id: int) -> bool:
        """
        Unit existence predicate
        :param: unit id
        :return: True if id exists, False if not
        """
        q = " SELECT (id) FROM units WHERE units.id={}; ".format(id)
        res = self.return_query_result(q)
        return len(res)>0


    def add_unit(self, study: int, name: str) -> int:
        """
        Adds a new unit into the units table. Unit names should be unique
        within a study. If the name already exists the function returns the id;
        otherwise it will create a new entry and return the id.
        :param study: the study id
        :param name: the name of the unit
        :return: (unit added, unit id)
        """
        cur = self.dbConnection.cursor()
        q = " SELECT (id) FROM units WHERE units.study={} AND units.name='{}';  ".format(study, name)
        res = self.return_query_result(q)
        
        unit_already_exists = len(res) > 0
        if unit_already_exists:
            return False, res[0][0]
        
        q = " SELECT MAX(id) FROM units; "
        res = self.return_query_result(q)  # find the biggest id
        max_id = res[0][0]
        if max_id is None:
            free_id = 0
        else:
            free_id = max_id + 1  # the next free id
        cur.execute("""
                    INSERT INTO units (id, name, study)
                    VALUES (%s, %s, %s);
                    """,
                    (free_id, name, study))  # insert the new entry
        self.dbConnection.commit()
        return True, free_id


    ###########################################################################
    # Bounds methods
    # These should be consolidated into a common function
    ###########################################################################
    def add_boundsint(self, study: int, measurementtype: int, minval: int, maxval: int) -> tuple:
        """
        Add bounds to the boundsint table
        TODO: the study doesn't really need to be supplied, it can be looked up
              in the measurementtype table
        TODO: check that the valtype field in measurementype matches
        :param study: the study
        :param measurementtype: the measurement type
        :param minval: minimum integer value
        :param maxval: maximum integer value
        :returns: True | False
        """
        if not (self.studyp(study) and
                self.measurementtypep(study)):
            return False, "Type 1"
        if not self.mt_in_studyp(study, measurementtype):
            return False, "Type 2"
        if not (check_int(minval) and check_int(maxval) and minval<=maxval):
            return False, "Type 3"
        
        cur = self.dbConnection.cursor()
        q = """
            SELECT measurementtype FROM boundsint
            WHERE boundsint.study={} AND boundsint.measurementtype={};
            """.format(study, measurementtype)
        res = self.return_query_result(q)
        if len(res) > 0:
            return False, "Type 4"
        cur.execute("""
                    INSERT INTO boundsint (measurementtype, minval, maxval, study)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (measurementtype, minval, maxval, study))
        self.dbConnection.commit()
        return True
    
    def add_boundsreal(self, study: int, measurementtype: int, minval: float, maxval: float) -> tuple:
        """
        Add bounds to the boundsreal table
        TODO: the study doesn't really need to be supplied, it can be looked up
              in the measurementtype table
        TODO: check that the valtype field in measurementype matches
        :param study: the study
        :param measurementtype: the measurement type
        :param minval: minimum integer value
        :param maxval: maximum integer value
        :returns: True | False
        """
        if not (self.studyp(study) and
                self.measurementtypep(study)):
            return False, "Type 1"
        if not self.mt_in_studyp(study, measurementtype):
            return False, "Type 2"
        if not (check_real(minval) and check_real(maxval) and minval<=maxval):
            return False, "Type 3"
        
        cur = self.dbConnection.cursor()
        q = """
            SELECT measurementtype FROM boundsreal
            WHERE boundsreal.study={} AND boundsreal.measurementtype={};
            """.format(study, measurementtype)
        res = self.return_query_result(q)
        if len(res) > 0:
            return False, "Type 4"
        cur.execute("""
                    INSERT INTO boundsreal (measurementtype, minval, maxval, study)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (measurementtype, minval, maxval, study))
        self.dbConnection.commit()
        return True
    
    def add_boundsdatetime(self, study: int, measurementtype: int, minval: int, maxval: int) -> tuple:
        """
        Add bounds to the boundsdatetime table
        TODO: the study doesn't really need to be supplied, it can be looked up
              in the measurementtype table
        TODO: check that the valtype field in measurementype matches
        :param study: the study
        :param measurementtype: the measurement type
        :param minval: minimum integer value
        :param maxval: maximum integer value
        :returns: True | False
        """
        if not (self.studyp(study) and
                self.measurementtypep(study)):
            return False
        if not self.mt_in_studyp(study, measurementtype):
            return False
        if not (check_datetime(minval) and check_datetime(maxval) and minval<=maxval):
            return False
        
        cur = self.dbConnection.cursor()
        q = """
            SELECT measurementtype FROM boundsdatetime
            WHERE boundsdatetime.study={} AND boundsdatetime.measurementtype={};
            """.format(study, measurementtype)
        res = self.return_query_result(q)
        if len(res) > 0:
            return False
        cur.execute("""
                    INSERT INTO boundsdatetime (measurementtype, minval, maxval, study)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (measurementtype, minval, maxval, study))
        self.dbConnection.commit()
        return True