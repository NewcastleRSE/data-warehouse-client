# e-Science Central Data Warehouse Tutorial
## Setting up a Data Warehouse
Add in PostgreSQL setup and DW creation here

## Caveats
The data warehouse connection does not handle exceptions well. generally a new connection to the DW needs to be made on an SQL command failure, using
```
dw = data_warehouse.DataWarehouse("db-credentials.json", "tutorial")
```

Most of the examples contain an zero-indexed "Test" entry. This is to maintain consistency with the `data_warehouse_guide.pdf` document. The table addition methods in the data warehouse client start `id` entries at zero.

There are some inconsistencies in maintenance of the study ID to which elements of certain tables are attached. For example both `add_boundsint()` and `add_measurementtype()` take a study `id`, but `boundsint` entries are linked to `measurementtype` entries and it should not be possible for them to refer to different study `id` values. These inconsistencies should be regarded as a bug which will be removed in future.


## Study format
### Clinical Evaluation Form "Q321"
| Measure | Description | Value Type | Categories (if norminal or ordinal) |
| --- | --- | --- | --- |
| G1 | Participant has read PIS | Nominal | Y<br>N |
| G3 | Year of Birth | DateTime | |
| G5 | Gender | Nominal | M<br>F<br>Prefer not to say |
| GC1 | Comorbidity: PTT | Nominal | Y<br>N |
| C14.5 | KCCQ clinical evaluation form, Item 5 | Ordinal | Every Night<br>3-4 Times per week<br>1-2 Times per week<br>Less than once a week<br>Never over the past 2 weeks |
| C5 | Name of drug | Text | |
| C5.1 | Dosage (mg) | Real | |
| X1 | Biopsy Date | DateTime | |

## Populating the DW using the client
- Set up a virtual environment
- Create a 'db-credentials.db' file

Connect to the database
```python
>>> from data_warehouse_client import data_warehouse
>>> dw = data_warehouse.DataWarehouse("db-credentials.json", "tutorial")
Loading credentials..
Connecting to the database..
Init successful! Running queries.

>>> 
```
### Adding studies
All alements of the data warehouse must or should be associated with a *study*. Inspecting the `study` table we can see that there are no studies present in a new data warehouse:
```python
>>> dw.get_studies()
[]
>>> 
```
We can do very little without a study to attach other elements to, so we should add a couple.
```python
>>> dw.add_study("Study Zero")
0
>>> dw.add_study("Test Data")
1
>>> dw.get_studies()
[('(0,"Study Zero")',), ('(1,"Test Data")',)]
>>> 
```
### Adding trials
None of the studies have any trials associated with them yet so we can add some. The `add_trial()` method takes a study ID and a text description of the trial. We will add some trials to studyid=1.
```python
>>> dw.add_trial(1, "Baseline")
0
>>> dw.add_trial(1, "6-month follow-up")
1
>>> dw.add_trial(1, "12-month follow-up")
2
>>> dw.get_trials_in_study(0)
[]
>>> dw.get_trials_in_study(1)
[('(0,1,Baseline)',), ('(1,1,"6-month follow-up")',), ('(2,1,"12-month follow-up")',)]
>>> 
```
Inspecting the data warehouse through `psql` will show the structure of the `trial` table now:
```
dw_tutorial=> SELECT * FROM trial;
 id | study |    description     
----+-------+--------------------
  0 |     0 | Baseline
  1 |     0 | 6-month follow-up
  2 |     0 | 12-month follow-up
(3 rows)

tutorial=> 
```
The client can be used to get trial IDs by study and description.
```python
>>> dw.get_trial_id_from_description(1, "Baseline")
(True, 0)
>>> dw.get_trial_id_from_description(0, "Baseline")
(False, None)
>>> dw.get_trial_id_from_description(1, "18-month follow-up")
(False, None)
>>> 
```
### Measurement groups
Measurements are captured in groups of one or more measurements and are best allocated to a *measurement group*. Measurement groups describe measurements related by their capture source or other meaningful grouping. Examples include: all questions in a survey; all emasurements taken from a body-worn data acquisition device; temperature, humidity and windspeed from an environmental monitor.

Our data warehouse is going to contain three types of measurement as shown in this `measurementgroup` table.

| id | description | study |
| --- | --- | --- |
| 0 | Test Group | 0 |
| 1 | Q321 | 1 |
| 2 | GFIT | 1 |
| 3 | Unilever Temperature Sensor | 1 |

We can add these to the data warehouse using the `add_measurementgroup()` method:
```
>>> dw.add_measurementgroup(0, "Test Group")
(True, 0)
>>> dw.add_measurementgroup(1, "Q321")
(True, 1)
>>> dw.add_measurementgroup(1, "GFIT")
(True, 2)
>>> dw.add_measurementgroup(1, "Unilever Temperature Sensor")
(True, 3)
>>> 
```
and we can check the status of our `measurementgroup` table using the `get_all_measurement_groups()` method, which returns a list of all measurement groups in a study. Notice that this function does not distinguish between studies which do not exist, and there being no measurement groups in the study.
```
>>> dw.get_all_measurement_groups(0)
[(0, 'Test Group')]
>>> dw.get_all_measurement_groups(1)
[(1, 'Q321'), (2, 'GFIT'), (3, 'Unilever Temperature Sensor')]
>>> dw.get_all_measurement_groups(2)
[]
>>> 
```
### Units
Many measurements till require units. The data warehouse does not itself perform units or dimensional checking, but it can store a textual description of the unit of a measurement. Units can easily be added to the data warehouse. It's a good idea to create units before creating measurement types (next section).
```
>>> dw.add_unit(1, "Test Unit")
(True, 0)
>>> dw.add_unit(1, "mg")
(True, 1)
>>> dw.add_unit(1, "metres")
(True, 2)
>>> dw.add_unit(1, "steps per minute")
(True, 3)
>>> dw.add_unit(1, "Centrigrade")
(True, 4)
>>> 
```
There is currently no inherent way of displaying the units table. However we can use the generic data warehouse `return_query_result()` method to execute an SQL query. *Note that issuing direct SQL commands should be used very sparingly and only if you know what you are doing!*
```
>>> dw.return_query_result("SELECT * FROM units;")
[(0, 'Test Unit', 1), (1, 'mg', 1), (2, 'metres', 1), (3, 'steps per minute', 1), (4, 'Centrigrade', 1)]
>>> 
```
### Measurement types
A *measurement type* contains information about a specific form of measurement that will be recorded in the data warehouse. A measurement type is defined by the *value type* (e.g. `int`, `real`, `datetime` etc.), the (optional) unit of measurement, and a label. A measurement type also must be attached to a specific study. This tutorial will implement a set of measurement types given in this table. The `valtype` field id reference are explained in Table 1 of `data_warehouse_clien.pdf`.

| id | study | description | units | valtype |
| --- | --- | --- | --- | --- |
| 0 | 0 | Test Type | | 4 |
| 1 | 1 | participant has read PIS | | 4 |
| 2 | 1 | Date of Birth | | 3 |
| 3 | 1 | Gender | | 5 |
| 4 | 1 | Comorbidity: PIT | | 4 |
| 5 | 1 | Name of Drug | | 2 |
| 6 | 1 | Dosage | 1 | 1 |
| 7 | 1 | Biopsy Date | | 3 |
| 8 | 1 | KCCQ clinical evaluation form, Item 5 | | 6 |
| 9 | 1 | AWS | 2 | 1 |
| 10 | 1 | Distance | 2 | 1 |
| 11 | 1 | Stride Length | 2 | 1 |
| 12 | 1 | Cadence | 3 | 1 |
| 13 | 1 | Temperature | 4 | 1 |

The `units` column ids refer to the `units` ids created in the previous section, so `1` is `mg`, `2` is `metres`, and so on.

Now we can add these measurement types to the data warehouse.
```
>>> dw.add_measurementtype(0, 4, "Test Type")
(True, 0)
>>> dw.add_measurementtype(1, 4, "participant has read PIS")
(True, 1)
>>> dw.add_measurementtype(1, 3, "Date of Birth")
(True, 2)
>>> dw.add_measurementtype(1, 5, "Gender")
(True, 3)
>>> dw.add_measurementtype(1, 4, "Comorbidity: PIT")
(True, 4)
>>> dw.add_measurementtype(1, 2, "Name of Drug")
(True, 5)
>>> dw.add_measurementtype(1, 1, "Dosage", 1)
(True, 6)
>>> dw.add_measurementtype(1, 3, "Biopsy Date")
(True, 7)
>>> dw.add_measurementtype(1, 6, "KCCQ clinical evaluation form, Item 5")
(True, 8)
>>> dw.add_measurementtype(1, 1, "AWS", 2)
(True, 9)
>>> dw.add_measurementtype(1, 1, "Distance", 2)
(True, 10)
>>> dw.add_measurementtype(1, 1, "Stride Length", 2)
(True, 11)
>>> dw.add_measurementtype(1, 1, "Cadence", 3)
(True, 12)
>>> dw.add_measurementtype(1, 1, "Temperature", 4)
(True, 13)
>>> 
```
As before we can examine the table using the generic data warehouse SQL command.
```
>>> dw.return_query_result("SELECT * FROM measurementtype;")
[(0, 'Test Type', 4, None, 0), (1, 'participant has read PIS', 4, None, 1), (2, 'Date of Birth', 3, None, 1), (3, 'Gender', 5, None, 1), (4, 'Comorbidity: PIT', 4, None, 1), (5, 'Name of Drug', 2, None, 1), (6, 'Dosage', 1, 1, 1), (7, 'Biopsy Date', 3, None, 1), (8, 'KCCQ clinical evaluation form, Item 5', 6, None, 1), (9, 'AWS', 1, 2, 1), (10, 'Distance', 1, 2, 1), (11, 'Stride Length', 1, 2, 1), (12, 'Cadence', 1, 3, 1), (13, 'Temperature', 1, 4, 1)]
>>> 
```
Within the PostgreSQL client this looks like:
```
dw_tutorial=# SELECT * FROM measurementtype;
 id |              description              | valtype | units | study 
----+---------------------------------------+---------+-------+-------
  0 | Test Type                             |       4 |       |     0
  1 | participant has read PIS              |       4 |       |     1
  2 | Date of Birth                         |       3 |       |     1
  3 | Gender                                |       5 |       |     1
  4 | Comorbidity: PIT                      |       4 |       |     1
  5 | Name of Drug                          |       2 |       |     1
  6 | Dosage                                |       1 |     1 |     1
  7 | Biopsy Date                           |       3 |       |     1
  8 | KCCQ clinical evaluation form, Item 5 |       6 |       |     1
  9 | AWS                                   |       1 |     2 |     1
 10 | Distance                              |       1 |     2 |     1
 11 | Stride Length                         |       1 |     2 |     1
 12 | Cadence                               |       1 |     3 |     1
 13 | Temperature                           |       1 |     4 |     1
(14 rows)

dw_tutorial=# 
```
### Categories
Some of the measurement types describe *categorical* data - `valtype` 4, 5 or 6 - and we must define the category structure in the data warehouse. this is accomplished by using the `add_category()` method.

**`dw.add_category`**(*study*, *cvalues*, *measurementtype*)  
> Add the categorical values in *cvalues* into the category table, referencing *study* and *measurementtype*. The values in *cvalues* should be in ascending order for ordinal categories; for cardinal and boolean types the order doesn't matter although the internal enumeration numbers will still be allocated in ascending order of the values given.
```
>>> dw.add_category(1, ["Y", "N"], 1)
True
>>> dw.add_category(1, ["Male", "Female", "Prefer not to say"], 3)
True
>>> dw.add_category(1, ["Y", "N"], 4)
True
>>> dw.add_category(1, ["Every Night", "3-4 times per week", "1-2 times per week", "L\
ess than once per week", "Never over the past 2 weeks"], 8)
True
>>> 
```
Examining this in `psql`:
```
dw_tutorial=# SELECT * FROM category;
 measurementtype | categoryid |        categoryname         | study 
-----------------+------------+-----------------------------+-------
               1 |          0 | Y                           |     1
               1 |          1 | N                           |     1
               3 |          0 | Male                        |     1
               3 |          1 | Female                      |     1
               3 |          2 | Prefer not to say           |     1
               4 |          0 | Y                           |     1
               4 |          1 | N                           |     1
               8 |          0 | Every Night                 |     1
               8 |          1 | 3-4 times per week          |     1
               8 |          2 | 1-2 times per week          |     1
               8 |          3 | Less than once per week     |     1
               8 |          4 | Never over the past 2 weeks |     1
(12 rows)

dw_tutorial=# 
```

### Bounded values
Integer, floating point (real) and datetime measurements can be bounded, that is, can be specified with a maximum and minimum value which is checked by the data warehouse when data is inserted. Let's create some bounded measurements and add them to the data warehouse.

#### Bounded ints (`valtype` 7)
Suppose a clinical evaluation form asks a patient "How hard is it to walk without an aid - give a number from 1 (easy) to 6 (impossible)". To create this measurement we first need to create a new `measurementtype` with a `valtype` of 7. We will add this to Study 1.
```
>>> dw.add_measurementtype(1, 7, "KCCQ clinical evaluation form, Item 10")
(True, 14)
>>> 
```
The bounds required bounds are added to the `boundsint` table using the `add_boundsint()` function, which takes the `measurementtype` id (returned from the `add_measurement()` method) as a parameter:
```
>>> dw.add_boundsint(1, 14, 1, 6)
True
>>> 
```
Examining the `boundsint` table in `psql` shows us the added bounds entry
```
dw_tutorial=# SELECT * FROM boundsint;
 measurementtype | minval | maxval | study 
-----------------+--------+--------+-------
              14 |      1 |      6 |     1
(1 row)

dw_tutorial=# 
```
#### Bounded reals (`valtype` 8)
We can do the same thing for bounded floating point numbers. The researchers have decided that the "Stride Length" should be subject to some constraints; no-one should have a stride longer than say 3.5m, and a measurement under 5cm doesn't count as a stride. The "Stride Length" measurement type already exists (with ID 11) so we can immediately add some bounds to the data warehouse. Note that the bounds must be given in the units of the measurement; the DW has no knowledge of the meaning of the units and cannot enforece this, it is up to the DW maintainer / researcher to ensure this.
```
>>> dw.add_boundsreal(1, 11, 0.05, 3.5)
True
>>> 
```
In `psql`:
```
dw_tutorial=# SELECT * FROM boundsreal;
 measurementtype | minval | maxval | study 
-----------------+--------+--------+-------
              11 |   0.05 |    3.5 |     1
(1 row)

dw_tutorial=# 
```
#### Bounded datetimes (`valtype` 9)
Lastley the DW allows bounded `datetime` types. Datetimes suppled to the DW client are Python `datetime.datetime` objects. Let's add a constraint on the "Biopsy Date" measurement type (id 7), which we have decided cannot have been carried out before 01/01/2022. We set a maximum date of some conveniently large time in the future in this case.
```
import datetime
>>> dw.add_boundsdatetime(1, 7, datetime.datetime(2022, 1, 1), datetime.datetime(2122, 1, 1))
True
>>> 
```
In `psql`,
```
dw_tutorial=# SELECT * FROM boundsdatetime;
 measurementtype | study |       minval        |       maxval        
-----------------+-------+---------------------+---------------------
               7 |     1 | 2022-01-01 00:00:00 | 2122-01-01 00:00:00
(1 row)

dw_tutorial=# 
```

### Connecting `measurementgroup`s to `measurementtype`s
So far we have defined a set of *measurement groups* and a set of *measurement types*, but they are currently not linked. Measurement groups exist to collect measurement types together, i.e. a `measurementgroup` has `measurementtype` members. The `connect_mt_to_mg()` method establishes a connection between a measurement type and a measurement group. Note that this table describes a many-to-many relationship, and `measurementtype`s can be members of multiple `measurementgroup`s.
```
>>> dw.connect_mt_to_mg(1, 1, 1, "G1")
True
>>> dw.connect_mt_to_mg(1, 2, 1, "G3")
True
>>> dw.connect_mt_to_mg(1, 3, 1, "G5")
True
>>> dw.connect_mt_to_mg(1, 4, 1, "GC1")
True
>>> dw.connect_mt_to_mg(1, 5, 1, "C5")
True
>>> dw.connect_mt_to_mg(1, 6, 1, "C5.1")
True
>>> dw.connect_mt_to_mg(1, 7, 1, "X1")
True
>>> dw.connect_mt_to_mg(1, 8, 1, "C14.5")
True
>>> dw.connect_mt_to_mg(1, 9, 2, "WB1")
True
>>> dw.connect_mt_to_mg(1, 10, 2, "WB2")
True
>>> dw.connect_mt_to_mg(1, 11, 2, "WB3")
True
>>> dw.connect_mt_to_mg(1, 12, 2, "WB4")
True
>>> dw.connect_mt_to_mg(1, 13, 3, "TS1")
True
>>> dw.connect_mt_to_mg(1, 14, 1, "C14.10")
True
>>> dw.get_all_measurement_groups(1)
[(1, 'Q321'), (2, 'GFIT'), (3, 'Unilever Temperature Sensor')]
>>> dw.get_all_measurement_groups_and_types_in_a_study(1)
[(1, 1, 'G1'), (1, 2, 'G3'), (1, 3, 'G5'), (1, 4, 'GC1'), (1, 5, 'C5'), (1, 6, 'C5.1'), (1, 7, 'X1'), (1, 8, 'C14.5'), (1, 14, 'C14.10'), (2, 9, 'WB1'), (2, 10, 'WB2'), (2, 11, 'WB3'), (2, 12, 'WB4'), (3, 13, 'TS1')]
>>> 
```
In `psql`:
```
dw_tutorial=# SELECT * FROM measurementtypetogroup;
 measurementtype | measurementgroup |  name  | study | optional 
-----------------+------------------+--------+-------+----------
               1 |                1 | G1     |     1 | f
               2 |                1 | G3     |     1 | f
               3 |                1 | G5     |     1 | f
               4 |                1 | GC1    |     1 | f
               5 |                1 | C5     |     1 | f
               6 |                1 | C5.1   |     1 | f
               7 |                1 | X1     |     1 | f
               8 |                1 | C14.5  |     1 | f
               9 |                2 | WB1    |     1 | f
              10 |                2 | WB2    |     1 | f
              11 |                2 | WB3    |     1 | f
              12 |                2 | WB4    |     1 | f
              13 |                3 | TS1    |     1 | f
              14 |                1 | C14.10 |     1 | f
(14 rows)

dw_tutorial=# 
```

### Sources and source types
All data added to the data warehouse comes from a `source`, e.g. a clinical evaluation form, algorithm or sensor. The data warehouse holds this information in two tables: `sourcetype`, which identifies generic information about a source; and `source`, which identifies specific sources (e.g. through unique identifiers). `source` entries are instances of `sourcetype`s, therefore `sourcetype`s should be created in the data warehouse first.

`sourcetype` entries can have an optional "version" label.
```
>>> dw.add_sourcetype(1, "Test Type")
0
>>> dw.add_sourcetype(1, "q321", 1)
1
>>> dw.add_sourcetype(1, "GFIT", 27)
2
>>> dw.add_sourcetype(1, "Unilever Temperature Sensor", 12)
3
>>> dw.get_sourcetypes(1)
[(0, 'Test Type'), (1, 'q321'), (2, 'GFIT'), (3, 'Unilever Temperature Sensor')]
>>> 
```
in `psql`:
```
dw_tutorial=# SELECT * FROM sourcetype;
 id |         description         | version | study 
----+-----------------------------+---------+-------
  0 | Test Type                   | NULL    |     1
  1 | q321                        | 1       |     1
  2 | GFIT                        | 27      |     1
  3 | Unilever Temperature Sensor | 12      |     1
(4 rows)

dw_tutorial=# 
```
Adding sources:
```
>>> dw.add_source(1, "Test")
0
>>> dw.add_source(1, 1)
1
>>> dw.add_source(2, 1)
2
>>> dw.add_source(3, 3267)
3
>>> 
```
`psql` (there's no Python funcion for querying the source table yet):
```
dw_tutorial=# SELECT * FROM source;
 id | sourceid | sourcetype | study 
----+----------+------------+-------
  0 | Test     |          1 |     1
  1 | 1        |          1 |     1
  2 | 1        |          2 |     1
  3 | 3267     |          3 |     1
(4 rows)

dw_tutorial=# 
```

### Adding participants
Measurements in a study can be, although don't have to be, associated with a *Participant*. Participants are added to the data warehouse with an `add_participant()` method. The `get_participants()` method returns a list of all of the participants attached to a study.
```
>>> dw.add_participant(1, "P123456")
0
>>> dw.get_participants(1)
[(0, 'P123456')]
>>> 
```

### Adding measurements
All of the previous sections have been required to prepare the appropriate groups and structures relevant to the data gathering process. It is important to consider the structure of the studies and trials, and the nature and origin of measurements, before adding any actual measurements to the data warehouse. With a correctly-defined data warehouse structure, data can be validated as it enters the data warehouse, and queries and analysis of data can be carried out efficiently.

In the tutorial example, we've collected the data in the following table.

| time | measurement group | group instance | measurement type | participant | study | trial | source | valtype | val (int) | val (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 08/03/2020 14:05 | 1 | 1 | 1 | 1 | 1 | | 1 | 4 | 1 | |
| 08/03/2020 14:05 | 1 | 1 | 2 | 1 | 1 | | 1 | 3 | | |
| 08/03/2020 14:05 | 1 | 1 | 3 | 1 | 1 | | 1 | 5 | 2 | |
| 08/03/2020 14:05 | 1 | 1 | 4 | 1 | 1 | | 1 | 4 | 0 | |
| 08/03/2020 14:05 | 1 | 1 | 5 | 1 | 1 | | 1 | 2 | | |
| 08/03/2020 14:05 | 1 | 1 | 6 | 1 | 1 | | 1 | 1 | | 2.50 |
| 08/03/2020 14:05 | 1 | 1 | 7 | 1 | 1 | | 1 | 3 | | |
| 08/03/2020 14:05 | 1 | 1 | 8 | 1 | 1 | | 1 | 6 | 3 | |
| 08/03/2020 14:05 | 1 | 1 | 14 | 1 | 1 | | 1 | 7 | 2 | |
| | | | | | | | | | | |
| 11/05/2020 11:03 | 2 | 9 | 9 | 1 | 1 | | 2 | 1 | | 4.30 |
| 11/05/2020 11:03 | 2 | 9 | 10 | 1 | 1 | | 2 | 1 | | 1.03 |
| 11/05/2020 11:03 | 2 | 9 | 11 | 1 | 1 | | 2 | 1 | | 22.00 |
| 11/05/2020 11:03 | 2 | 9 | 12 | 1 | 1 | | 2 | 1 | | 5.30 |
| | | | | | | | | | | |
| 11/05/2020 11:03 | 3 | 13 | 13 | 1 | 1 | | 3 | 1 | | 37.50 |
| 11/05/2020 11:03 | 3 | 13 | 13 | 1 | 1 | | 3 | 1 | | 36.40 |
| 11/05/2020 11:03 | 3 | 13 | 13 | 1 | 1 | | 3 | 1 | | 35.80 |
