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
### Study table
Check the `study` table:
```python
>>> dw.get_studies()
[]
>>> 
```
There are currently no studies in the data warehouse. so we should add a couple.
```python
>>> dw.add_study("Study Zero")
>>> dw.add_study("Test Data")
>>> dw.get_studies()
[('(0,"Study Zero")',), ('(1,"Test Data")',)]
>>> 
```
### Trial table
No client code yet so do this in `psql`:
```sql
tutorial=> INSERT INTO
tutorial-> trial (id, study, description)
tutorial-> VALUES
tutorial-> (0, 0, 'Baseline'),
tutorial-> (1, 0, '6-month follow-up'),
tutorial-> (2, 0, '12-month follow-up');
INSERT 0 3
tutorial=> SELECT * FROM trial;
 id | study |    description     
----+-------+--------------------
  0 |     0 | Baseline
  1 |     0 | 6-month follow-up
  2 |     0 | 12-month follow-up
(3 rows)

tutorial=> 
```
Then in the python client:
```python
>>> dw.get_trial_id_from_description(0, "Baseline")
(True, 0)
>>> 
```