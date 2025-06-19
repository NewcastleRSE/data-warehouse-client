SHELL = /bin/bash
CP = cp
MV = mv
MKDIR = mkdir -p
RM = rm -f
RM_R = rm -fr

DOCKER = sudo docker
COMPOSE = $(DOCKER) compose -v


###############################################################################
# Load .env file
###############################################################################
ENV_FILE = .env
ENV_FILE_DEFAULT = .env.default
ifneq ("$(wildcard .env)","")
  include .env
  export
else
endif

COMPOSE_TEMPLATE=compose-template.yaml
COMPOSE_FILE=compose.yaml

CLIENT_DOCKER_DIR=./containers/client
SCRIPTS_DIR=./resources/scripts


###############################################################################
# Orchestration
###############################################################################
up : $(OUTPUT_DIR) $(INIT_FILES) $(DW_CREDFILE) client compose-file
	$(COMPOSE) up

down :
	$(COMPOSE) down

restart :
	$(COMPOSE) down
	$(COMPOSE) up

client : ${CLIENT_DOCKER_DIR}/Dockerfile
	$(COMPOSE) build

compose-file : env-make-secrets $(COMPOSE_TEMPLATE)
	@$(SHELL) -c "export $(grep -v '^#' ${ENV_FILE} | xargs) && envsubst < ${COMPOSE_TEMPLATE} > ${COMPOSE_FILE}"


###############################################################################
# Environment
###############################################################################
#test :
#sudo docker run -rm --name some-postgres -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -d -p 5432:5432 postgres:14.17

$(ENV_FILE) : $(ENV_FILE_DEFAULT)
	$(SHELL) $(SCRIPTS_DIR)/env-copy-secrets.sh

env-make-secrets : $(ENV_FILE)
	$(SHELL) $(SCRIPTS_DIR)/env-make-secrets.sh

$(DW_CREDFILE) : $(ENV_FILE)
	$(SHELL) $(SCRIPTS_DIR)/client-make-creds.sh
	$(MV) $@ $(CLIENT_DOCKER_DIR)


###############################################################################
# Database initialisation
###############################################################################
INIT_FILES = 01.sql 02.sql
INIT_DATA_DIR = ${COMPOSE_MOUNT_INITDATA}
SCHEMA_DIR = ../../schema
OUTPUT_DIR = ${COMPOSE_MOUNT_LOCAL}

mount-points: $(OUTPUT_DIR) $(INIT_DATA_DIR) $(INIT_FILES)

$(OUTPUT_DIR) :
	$(MKDIR) $@

$(INIT_DATA_DIR) :
	$(MKDIR) $@

01.sql : $(SCHEMA_DIR)/basic_dw_roles.sql
	$(CP) $< $(INIT_DATA_DIR)/$@

02.sql : $(SCHEMA_DIR)/basic_dw_schema.sql
	$(CP) $< $(INIT_DATA_DIR)/$@



###############################################################################
# Clean
###############################################################################
clean-all: clean clean-outputs

clean:
	$(RM) $(ENV_FILE) $(COMPOSE_FILE) $(CLIENT_DOCKER_DIR)/$(DW_CREDFILE)
	$(RM_R) $(INIT_DATA_DIR)

clean-outputs:
	sudo $(RM_R) $(OUTPUT_DIR)
