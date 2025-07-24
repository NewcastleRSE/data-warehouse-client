## Module Contents
The `data_warehouse` module contains basic functions for interacting with a data warehouse instance.

### `measurement` table functions
data_warehouse.**get_measurements(** *study*, *participant=-1*, *measurement_type=-1*, *measurement_group=-1*, *measurement_group_instance=-1*, *trial=-1*, *start_time=-1*, *end_time=-1* **)**
<ul>
<li style="list-style-type: none;">

Retrieve a list of measurements from a data warehouse.

</li>
<li style="list-style-type: none;">

*study* is the integer id of the `study` containing the measuremtents.

All other arguments are optional. If no optional arguments are supplied then the entire measurement table for the study will be returned. This could potentially be very large.

*start_time* and *end_time* should be `datetime` objects. While the function will accept a properly formatted ISO8601 date string, a `datetime` object is robust. Future versions of the client may remove the acceptance of dates as strings.

</li>
</ul>

data_warehouse.**get_measurements_with_value_test(** *study*, *measurement_type*, *value_test_condition*, *participant=-1*, *measurement_group=-1*, *measurement_group_instance=-1*, *trial=-1*, *start_time=-1*, *end_time=-1* **)**
<ul>
<li style="list-style-type: none;">

Retrieve a list of measurements of a specified *measurement_type* subject to a *value_test_condition*.

</li>
<li style="list-style-type: none;">

*study* is the integer id of the `study` containing the measurements. *measurement_type* and a *value_test_condition* must be specified. All other arguments are optional. *value_test_condition* must be a valid SQL value expression postfix operator corresponding to the *measurement_type*. For example, if *measurement_type = 1*, i.e. a `valreal`, then *" > 5.0"* would be a valid *value_test_condition* that selects all values of the *measurement_type* greater than 5.0.

*start_time* and *end_time* should be `datetime` objects. While the function will accept a properly formatted ISO8601 date string, a `datetime` object is robust. Future versions of the client may remove the acceptance of dates as strings.

</li>
</ul>

