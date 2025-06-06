
# Writing Loaders for the Data Warehouse – a User Guide

## Changelog
| Version | Date | Author | Comments |
| --- | --- | --- | --- |
| v1.1.0 | Sep 2024 | [Paul Watson](mailto:paul.watson%40newcastle.ac.uk), Newcastle University | |
| v1.2.0 | Jun 2025 | [Robin Wardle](mailto:robin.wardle%40newcastle.ac.uk), Newcastle University | Updated for 5GIR project |


## Introduction and terminology
The e-Science Central Data Warehouse was designed to enable healthcare study data to be stored and analysed. Data can be inserted into the data warehouse in multiple ways: by inserting a reading at a time through the client; by directly interacting with SQL; by pasting data into a graphical database client (e.g. pgAdmin4); or by bulk uploading data from a file. This document describes this latter case of using loaders written in Python to populate the data warehouse.

The data warehouse offers a data loading module which is moderately complex but which ensures that appropriate types, bounds and primary and secondary key constraints are all satisfied when attempting to insert data. The loading module has the following concepts.

| Entity | Python type | Description |
| --- | --- | --- |
| Data | DataToLoad | A dictionary describing a measurementgroupinstance |
| Loader Function | Loader | A Python function which inserts all of the individual measurements in a DataToLoad instance into the data warehouse `measurement` table |
| Loader Name | data_name | A `str` holding a text name for a Python loader function |
| Loader Mapper | mapper | A dictionary which maps a Loader Name to a Loader Function|
| Bounds | Bounds | A list of numeric and categorical bounds and limits to be checked by the Loader Function during data insertion |

To recap from the data warehouse design document:
- a `measurementtype` is a specification of a unique type of measurement (e.g. `int`, `category`)
- a `measurementgroup` is a collection of `measurementtypes`, defined as a many-to-many mapping in a `measurementtypetogroup`.
- a `measurement` is a single value of a `measurementtype` recorded in the data warehouse
- a `measurementgroupinstance` is a labelling of the set of `measurementtypes` in a `measurementgroup` all recorded at the same time.

Put another way, `measurementgroups` form mini-tables of `measurementtypes` - the specification of each mini-table is done through `measurementtypetogroup` mappings. A `measurementgroupinstance` is the equivalent of a single row entry in a `measurementgroup` table, with each actual value recorded being a `measurement`.


## Data loading types
Data to be stored in the data warehouse must first be prepared by transforming it into a Python dictionary which is defined in the data warehouse client as the type `DataToLoad`, which describes a full or partial *measurementgroup*.

```python
DataToLoad = Dict[str, Union[Value, List['DataToLoad'], List[str]]]
```
where
```python
Value = Union[int, float, str, DateTime]
```

An instance of data of type `DataToLoad` is a *measurementgroupinstance*. Each dictionary key has the same name as the corresponding *measurementtype* that data entity is taken from.

The `DataToLoad` dictionary entry value is defined as a `Union` of types. The dictionary entry value can thus take **one** of the types specified in the type definition.

| Type name | Permitted types | Examples |
| --- | --- | --- |
| `Value` | `int`, `float`, `datetime`, `str` | A duration in seconds, e.g. `108` |
| `List['DataToLoad']` | Another list of dictionaries | Data on members of a family |
| `List[str]` | A list of `str` types | A set of options, e.g. `['sticks', 'wheelchair', 'roller']` |

Note that in this document, `real` and `float` are used interchangeably. `real` is a data warehouse type and is functionally identical (defined to be equivalent) to Python's `float` type.


## Client data loading facility
The data loading functions are found in the `data_warehouse.load_data` module. Loading data from an instance of `DataToLoad` is performed by a call to `data.warehouse.load_data.load_data()`, the function definition being defined below.

```python
def load_data(  data_warehouse_handle,
                data: DataToLoad, 
                data_name: str, 
                mapper: Dict[str, Loader], 
                study: Study, 
                bounds: Bounds = None, 
                trial: Optional[Trial] = None, 
                participant: Optional[Participant] = None, 
                source: Optional[Source] = None, 
                cursor=None) -> Tuple[bool, List[MeasurementGroupInstance], List[str]]:
""" 
Load one item of data into the datawarehouse. 
:param data_warehouse_handle: handle to access the data warehouse 
:param data: the data item containing the fields to be loaded 
:param data_name: the name of the type of data: this is used to find the correct loader 
:param mapper: a dictionary mapping from data_name to the loader function 
:param study: study id in the data warehouse 
:param bounds: tuple holding bounds used to check data 
:param trial: optional trial id 
:param participant: optional participant id (must already be in the warehouse) 
:param source: optional source id
:param cursor: an optional cursor for accessing the datawarehouse 
:return: Success?, list of measurement group instance ids for the measurement groups inserted, error messages 
"""
```

The optional `Bounds` parameter provides the data warehouse loading function with validation information against which the `DataToLoad` instance is checked during insertion.
- Bounded values (`bounded int`, `bounded real` and `bounded datetime`) must lie between the minimum and maximum limits inclusive as stored in the appropriate bounded limits tables. E.g., if a `bounded int` can lie between 1 and 3, then a value of 5 will be rejected.
- Categorical variables must have ids and values that are stored in the data warehouse category table. e.g., if declared categories are `(1, 'bungalow')`, `(2, 'flat')`, `(3, 'multi-storey house')` then an id of 4, or a category value of 'apartment' would be rejected.

The format of the `Bounds` parameter is
```python
Bounds = Tuple [
    IntBounds,
    RealBounds,
    DateTimeBounds,
    CategoryIds,
    CategoryValues
]
```

If the `Bounds` parameter is omitted then its value will be generated from the data warehouse dimension tables `boundsint`, `boundsreal`, `boundsdatetime` and `category`. In general it's better practice to add measurement limits to the data warehouse dimension tables but if this data has not been committed, e.g. if it's not known *a priori* - maybe it's returned from the instrument during measurement - or if it needs to be overridden, then the `Bounds` parameter can be used.

The `mapper` dictionary is a mapping from string keys to the names of individual data loading functions. The `data_name` string is used as the key in the `mapper` parameter to select the loader function that picks out the values of the fields in the data so that they can be loaded into the warehouse.

## Loader Function 
A set of library functions must be provided by the data warehouse designer or administrator to load each of the different types of data into the warehouse. The signature of a loader is:

```python
data: DataToLoad, bounds: Bounds -> LoaderResult
```
The type of `LoaderResult` is:
```
Tuple [
    List[Tuple[MeasurementGroup, List[LoadHelperResult]]],
    Optional[DateTime],
    Optional[Trial],
    Optional[Participant],
    Optional[Source]
]
```

The `MeasurementGroup` parameter is the id of the Measurement Group to be loaded. If the `DateTime`, `Trial`, `Participant` and Source value are present then they will be associated with each measurement inserted into the Data Warehouse. `LoadHelperResult` is explained in the next section.

### Loading a Field
A loader function is responsible for loading in each field that makes up an instance of a measurement group. To do this, the loader function calls the client field loaders that are defined in the client module `data_warehouse.import_with_checks`. Each field loader is of type:
```python
MeasurementType, DataToLoad, field: str -> LoadHelperResult
```
or (for fields where the `Bounds` need to be checked):
```python
MeasurementType, DataToLoad, field: str, Bounds -> LoadHelperResult
```

These functions return a value describing the success or otherwise of the operation in `LoadHelperResult`, which is of type `Tuple[bool, List[ValueTriple], str]`. The type `ValueTriple = Tuple[MeasurementType, ValType, Value]`
 
The three fields in the `LoadHelperResult` Tuple are:
- A `bool` that is `True` if loading of the field was successful
- A `List` of `ValueTriples`, where each triple represents a value to be loaded into the data warehouse.
- A string that holds an error message if the first field of the tuple is `False`
 
 Field Loaders that cover all the types of data that the data warehouse can store are provided in the `import_with_checks` module

#### Regular types
```python
mk_int
mk_optional_int
mk_real
mk_optional_real
mk_string
mk_optional_string
mk_datetime
mk_optional_datetime
mk_boolean
mk_optional_boolean
```
#### Categorical types from ids
```python
mk_nominal_from_id
mk_optional_nominal_from_id
mk_ordinal_from_id
mk_optional_ordinal_from_id
```
#### Categorical types from ids in a string
```python
mk_categorical_from_id_in_string
mk_nominal_from_id_in_string
mk_optional_nominal_from_id_in_string
mk_ordinal_from_id_in_string
mk_optional_ordinal_from_id_in_string
```
#### Categorical types from values
```python
mk_categorical_from_value
mk_nominal_from_value 
mk_optional_nominal_from_value
mk_ordinal_from_value
mk_optional_ordinal_from_value
```
#### Bounded types
```python
mk_bounded_int
mk_optional_bounded_int
mk_bounded_real
mk_optional_bounded_real
mk_bounded_datetime
mk_optional_bounded_datetime
```
#### External types
```python
mk_external
mk_optional_external
```

Note that each loader has two versions – one if the field is optional, and the other if it is mandatory.

The Loader function must return a tuple of type `LoaderResult` which is defined as:
```python
LoaderResult =  Tuple [
    List[Tuple[MeasurementGroup, List[LoadHelperResult]]],
    Optional[DateTime],
    Optional[Trial],
    Optional[Participant],
    Optional[Source]
]
```  

The fields in `LoaderResult` are:
- a list of tuples holding the measurement group id, and the results of reading in each measurement type from the dictionary. We will explain in the loading lists section below why a list of tuples can be returned.
- An optional value for the DateTime field stored with each measurement in the measurement group instance. If it is not provided then the time value stored with each  measurement in the data warehouse will be set to the time that the measurement group instance was inserted into the data warehouse.
- An optional value for the Trial id to be stored with each measurement in the measurement group instance. If this is not provided then the value of the Trial will be given a null value for each measurement stored in the data warehouse.
- An optional value for the Participant id to be stored with each measurement in the measurement group instance. If this is not provided, then the value of Participant will be set to a null value for each measurement stored in the data warehouse.
- An optional value for the Source id to be stored with each measurement in the measurement group instance. If this is not provided, then the value of Source it will be set to a null value  for each measurement stored in the data warehouse.  

### Categorial Field Loaders 
There are three variants of each categorical loader: 
- `load_*_from_id` : load the integer id of the category
- `load_*_from_id_in_string` : load the integer id of the category when it is encoded in a string
- `load_*_from_value` : load the value of the category; this is a string

where * is `nominal` or `ordinal`.

For example, here is a loader for a measurement group (with an id of 40) holding information on a drug taken by a participant. This group contains two measurement types: a string that holds the name of the drug (measurement type 400), and an integer holding the dose (measurement type 401):

```python
def drugs_loader(data: DataToLoad, bounds: Bounds) -> LoaderResult: 
    drug_mg_id: MeasurementGroup = 40 
    drug_mgi = [(drug_mg_id, 
                 [iwc.load_string(400, data, 'drug'), 
                  iwc.load_int(401, data, 'dose')] 
                 )] 
    return drug_mgi, None, None, None, None
```
 
### Loading Sets 
A set is where the field being loaded holds a set of elements. As the data warehouse has no concept of sets, each possible element is represented by a different `measurementtype`, with valtype set to Boolean. Therefore, the `load_a_set` loaders have the following types:

```python
load_set(
        measurement_types: List[MeasurementType],
        data: DataToLoad,
        field: str,
        value_list: List[str]
        ) -> LoadHelperResult
    load_optional_set(
        measurement_types: List[MeasurementType], data: DataToLoad, field: str, value_list: List[str]) -> LoadHelperResult  
```

The `measurement_types` field gives a list of the ids of the measurement types, while the `value_list` gives a list of the elements corresponding to each `measurement_type`. The list retrieved from the field in the dictionary must be a subset of the `value_list`. For example, if the `measurement_types = [100,101,102]` and value_list is: `[“red”, “green”, “blue”]` and the field in the dictionary holds `[“red”, “blue”]` then
- the value in the instance of `measurement_type 100` will be set to `True`
- the value in the instance of `measurement_type 101` will be set to `False`
- the value in the instance of `measurement_type 102` will be set to `True`.

### Loading Lists
A field in the dictionary to be loaded into the data warehouse may contain a list of elements. The following functions load lists:

```python
load_list(
    data: DataToLoad,
    field: str,
    loader: Callable[[DataToLoad], LoaderResult],
    mg_id: MeasurementGroup,
    bounds: Bounds
    ) -> List[Tuple[MeasurementGroup, List[LoadHelperResult]]]

load_optional_list(
    data: DataToLoad,
    field: str,
    loader: Callable[[DataToLoad], LoaderResult],
    mg_id: MeasurementGroup,
    bounds: Bounds
    ) -> List[Tuple[MeasurementGroup, List[LoadHelperResult]]] 
```

In each list loader, as well as the usual data, field and bounds parameters, there are also:
- `loader`: a loader function to load a measurement group instance from each element of the list (e.g., `drugs_loader`)
- `mg_id`: the measurement group id of the current measurement group instance

## Example data loader
This example can be found in the data warehouse `tests` subdirectory.

A data warehouse is used to house medical data associated with some measurements on a patient's walking characteristics along with drugs that the patient may be taking. The data (in the `DataToLoad` type format) is provided as

```python
data = {
    'visit-date': datetime.now(),
    'visit-code': 'visit3',
    'wb_id': "fred",
    'Turn_Id': 2345,
    'Turn_Start_SO': 12.5,
    'Turn_End_SO': 123.3,
    'Turn_Duration_SO': 103.0,
    'Turn_PeakAngularVelocity_SO': 99.9,
    'drugs': [{'drug': 'asprin', 'dose': 10}, {'drug': 'calpol', 'dose': 30}, {'drug': 'clopidogrel', 'dose': 20}]
}
```

It can be seen that the data is structured in (expanded form) as

```python
Dict[str, int | float | str | datetime | List[DataToLoad] | List[str]]
```

```python
mapper {
        "walking_and_drugs": walking_and_drugs_loader,
        "test_all": check_all_loader,
        "test_all_2": check_all_loader_2
    }
```

`walking_and_drugs_loader` function that reads in an instance of a measurement group (with an id of 39) holding information on some walking features measured for a participant. The “data” dictionary also has a field (“drugs”) that holds a list of information to be loaded on the drugs taken by the participant. Each of the elements of this list is read in by the drugs_loader function described earlier, and this results in a new instance of the measurement group 40 being loaded into the data warehouse for each element in the list.

The result of the `walking_and_drugs_loader` function is therefore a set of measurement group instances ready to be loaded into the data warehouse (assuming there are no errors). This set contains one instance of measurement group 39, and multiple instances of measurement group 40 - one instance for each drug the patient is taking.


```python
def walking_and_drugs_loader(data: DataToLoad, bounds: Bounds)  -> LoaderResult:
    turn_group: MeasurementGroup = 39
    turn_group_instance: List[Tuple[MeasurementGroup, List[LoadHelperResult]]] = [
        (turn_group,
            [
                iwc.load_datetime(370, data, 'visit-date'),
                iwc.load_string(371, data, 'visit-code'),
                iwc.load_string(1839, data, 'wb_id'),
                iwc.load_int(1843, data, 'Turn_Id'),
                iwc.load_real(1844, data, 'Turn_Start_SO'),
                iwc.load_real(1845, data, 'Turn_End_SO'),
                iwc.load_real(1846, data, 'Turn_Duration_SO'),
                iwc.load_real(1847, data, 'Turn_PeakAngularVelocity_SO')
            ]
        )
    ] 
    drug_group_instances: List[Tuple[MeasurementGroup, List[LoadHelperResult]]] = \
        iwc.load_list(data, 'drugs', drugs_loader, turn_group, bounds)
    return turn_group_instance+drug_group_instances, None, None, None, None 
```