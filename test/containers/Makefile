SHELL = /bin/bash
CP = cp
MKDIR = mkdir -p

DOCKER = sudo docker
COMPOSE = $(DOCKER) compose



###############################################################################
# Load .env file
###############################################################################
ENVFILE = .env
ENVFILE_DEFAULT = .env.default
ifneq ("$(wildcard .env)","")
  include .env
  export
else
endif

COMPOSE_TEMPLATE=compose-template.yaml
COMPOSE_FILE=compose.yaml


###############################################################################
# Orchestration
###############################################################################
up : env-make-secrets compose-file $(DW_CREDFILE) client
	$(COMPOSE) up

down : $(ENVFILE)
	$(COMPOSE) down

client : Dockerfile
	$(COMPOSE) build

compose-file : env-make-secrets $(COMPOSE_TEMPLATE)
	$(SHELL) -c "export $(grep -v '^#' ${ENVFILE} | xargs); envsubst < ${COMPOSE_TEMPLATE} > ${COMPOSE_FILE}"


###############################################################################
# Environment
###############################################################################
test :
	sudo docker run -rm --name some-postgres -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -d -p 5432:5432 postgres:14.17

$(ENVFILE) : $(ENVFILE_DEFAULT)
	$(SHELL) env-copy-secrets.sh

env-make-secrets : $(ENVFILE)
	$(SHELL) env-make-secrets.sh

$(DW_CREDFILE) : $(ENVFILE)
	$(SHELL) client-make-creds.sh


###############################################################################
# Database initialisation
###############################################################################
INIT_FILES = 01.sql 02.sql
INIT_DATA_DIR = ./initdata
SCHEMA_DIR = ../../schema

init-data : $(INIT_DATA_DIR) $(INIT_FILES)

$(INIT_DATA_DIR) :
	$(MKDIR) $@

01.sql : $(SCHEMA_DIR)/basic_dw_roles.sql
	$(CP) $< $(INIT_DATA_DIR)/$@

02.sql : $(SCHEMA_DIR)/basic_dw_schema.sql
	$(CP) $< $(INIT_DATA_DIR)/$@
