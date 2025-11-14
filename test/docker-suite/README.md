# Data Warehouse Test Framework

## Overview
The data warehouse client test framework uses a Docker-based system implementing the following three containers

- a database (PostgreSQL)
- a Python environment
- an admin tool (adminer)

This Docker-based environment allows the effective testing and also development of the data warehouse client with the following advantages

- a dedicated database deployment, either through a local installation, or in the cloud, is not required
- local Python environment management is not required
- different databases or Python versions can be tested by changing the Docker configuration rather than by awkward and tedious local version management
- credentials are ephemeral, generated and deleted locally and on-the-fly, so there is no need to manage these separately
- testing can be automated on e.g. GitHub actions without requiring prior database installation
- all aspects of the data warehouse can be tested, from table setup to client interaction and SQL response
- either the built-in tests can be run as default or the test suite can be modified to run and test user scripts, e.g. loaders

The use of an admin tool (adminer) provides extra interactive flexibility when developing, debugging or testing the data warehouse.

## Requirements
- a Linux-based operating system or similar implementing `bash`
- Docker
- `make`

## Quickstart
The test suite is `make`-based and is run from the `test/docker-suite` subdirectory. To create the containers and run the tests, in a `bash` shell type

```
make .env
make up
```

Test results are written to an `./outputs` folder. Once complete the terminal remains connected to `docker-compose`, allowing further connection to the containers if needed. To stop and delete the test environment, in the same shell type

```
ctrl-c
make down
```

The generated environment and other intermediate files used in the framework creation (including generated database credentials) can be removed with

```
make clean-all
```

## The test environment
The client test environment uses `docker-compose` to manage the three containers - database, python, and admin tool. The configuration is template based with the following files describing the base configuration:

- `compose-template.yaml`
- `.env.default`

Running `make up` first executes some configuration scripts in `resources/scripts` which parse the configuration templates and create two configuration file instances from the templates

- `compose.yaml`
- `.env`

The critical operations performed in this process are database credential generation and template variable substitution (mainly for paths etc). A data warehouse client credentials file (`testdb-credentials.json`) is also created, which is used by the client test suite to connect to the database instance.

The `docker-compose` file controls the generation of the databse container including the setup of the data warehouse table structure. The creation of the Python client container uses a Dockerfile in `containers/client`, and this can be configured to use the local working data warehouse repository (default) or a data warehouse at a remote URL (useful for testing user scripts on a stable data warehouse release). The client subdirectory also contains the default test framework, Python test files and a Docker command for connecting to the Python client container in terminal mode.

## Limitations
The client test environment is not currently designed to test the integrity of the database itself, although it could be. Client functions could be tested using this framework or through mock functions in the root repository `test` subdirectory.
