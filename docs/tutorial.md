# e-Science Central Data Warehouse Tutorial
## Setting up a Data Warehouse
Add in PostgreSQL setup and DW creation here

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
>>> dw.add_study("Test Data")
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
| 1 | Q321 | 1 |
| 2 | GFIT | 1 |
| 3 | Unilever Temperature Sensor | 1 |

To Be Continued ...
