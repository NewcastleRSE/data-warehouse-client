/* Create essential roles */

CREATE ROLE dw;
CREATE ROLE data_warehouse_read_only;
CREATE ROLE data_warehouse_read_write;

GRANT dw TO pgadmin;           /* Replace "pgadmin" with superuser name */
