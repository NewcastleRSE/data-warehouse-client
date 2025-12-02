## Module Contents
The `csv_io` module contains the following functions:

csv_io.**export_measurements_as_csv(** *rows*, *file* **)**
<ul>
<li style="list-style-type: none;">

Open *file* and write *rows* to it.

</li>
<li style="list-style-type: none;">

*rows* is a list object containing a series of other list objects. Each contained list object is a *row* corresponding to a measurement from the `measurement` table in the data warehouse. The *rows* object should be produced by one of the data warehouse measurement query functions `get_measurements()` or `get_measurements_with_value_tests()`.

</li>
</ul>

csv_io.**export_measurement_groups_as_csv(** *header*, *instances*, *file* **)**
<ul>
<li style="list-style-type: none;">

Open *file* and write the header text in *header*, and then data in *instances* to it.

</li>
<li style="list-style-type: none;">



</li>
</ul>
