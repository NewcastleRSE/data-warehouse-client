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


from csv import writer


def export_measurements_as_csv(rows, file):
    """
    Saves measurements returned by queries in a CSV file

    :param rows: a list of rows returned by one of the following functions:
        get_measurements()
        get_measurements_with_value_test()
        get_measurement_group_instances_with_value_tests()

    :param fname: the filename of the output CSV file
        The output file has a header row, followed by a row for each measurement. This has the columns:
            id,time,study,participant,measurementType,typeName,measurementGroup, groupInstance,trial,valType,value
    """
    with open(file, "w", newline="", encoding="utf-8") as f:
        wr = writer(f)
        wr.writerow(
            ["Id", "Time", "Study", "Participant", "Measurement Type", "Measurement Type Name", "Measurement Group",
             "Measurement Group Instance", "Trial", "Value Type", "Value"])
        wr.writerows(rows)


def export_measurement_groups_as_csv(header, instances, file):
    """
    Stores measurements returned by formMeasurementGroups in a CSV file
    The input rows must be in the format produced by formMeasurementGroups
    The output file has a header row, followed by a row for each measurement group instance. The table has columns:
        groupInstance,time of first measurement in instance,study,participant,measurementGroup,trial,
                value1, value2....
            where value n is the value for the nth measurement in the instance (ordered by measurement type)
    :param header: a list of column names
    :param instances: a list of instances returned by formatMeasurementGroup
    :param fname: the filename of the output CSV file
    """
    with open(file, "w", newline="", encoding="utf-8") as f:
        wr = writer(f)
        wr.writerow(header)
        wr.writerows(instances)
