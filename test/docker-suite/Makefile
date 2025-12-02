# Copyright 2020 Newcastle University.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

###############################################################################
# Makefile for e-Science Central Data Warehouse testing
# Run in 2 stages:
#     - make .env
#     - make up
###############################################################################
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
.PHONY : up test down restart client

up test: $(OUTPUT_DIR) 01.sql 02.sql $(DW_CREDFILE) ${COMPOSE_FILE} client
	$(COMPOSE) up --build

down :
	$(COMPOSE) down

restart :
	$(COMPOSE) down
	$(COMPOSE) up --build

client : ${CLIENT_DOCKER_DIR}/$(COMPOSE_SERVICE_CLIENT_DOCKERFILE)
	$(COMPOSE) build

${COMPOSE_FILE} : ${ENV_FILE} $(COMPOSE_TEMPLATE)
	@$(SHELL) -c "export $(grep -v '^#' ${ENV_FILE} | xargs) && envsubst < ${COMPOSE_TEMPLATE} > ${COMPOSE_FILE}"


###############################################################################
# Environment
###############################################################################
$(ENV_FILE) : $(ENV_FILE_DEFAULT)
	$(SHELL) $(SCRIPTS_DIR)/env-copy-secrets.sh
	$(SHELL) $(SCRIPTS_DIR)/env-make-secrets.sh

$(DW_CREDFILE) : $(ENV_FILE)
	$(SHELL) $(SCRIPTS_DIR)/client-make-creds.sh
	$(CP) $@ $(CLIENT_DOCKER_DIR)/test-framework
	$(MV) $@ $(CLIENT_DOCKER_DIR)/test-override


###############################################################################
# Database initialisation
###############################################################################
INIT_FILES = 01.sql 02.sql
INIT_DATA_DIR = ${COMPOSE_MOUNT_INITDATA}
SCHEMA_DIR = ../../schema
OUTPUT_DIR = ${COMPOSE_MOUNT_LOCAL}

init-files : $(INIT_FILES)

mount-points : $(OUTPUT_DIR) $(INIT_DATA_DIR) $(INIT_FILES)

$(OUTPUT_DIR) :
	$(MKDIR) $@

$(INIT_DATA_DIR) :
	$(MKDIR) $@

01.sql : $(SCHEMA_DIR)/basic_dw_roles.sql $(INIT_DATA_DIR)
	sudo $(CP) $< $(INIT_DATA_DIR)/$@

02.sql : $(SCHEMA_DIR)/basic_dw_schema.sql $(INIT_DATA_DIR)
	sudo $(CP) $< $(INIT_DATA_DIR)/$@



###############################################################################
# Clean. Make sure to check directories exist.
###############################################################################
.PHONY : clean clean-all clean-env clean-misc clean-dirs

clean: clean-misc clean-dirs

clean-all clean-env: clean-misc clean-dirs
	$(RM) $(ENV_FILE)

clean-misc:
	$(RM) $(COMPOSE_FILE)
ifdef DW_CREDFILE
	$(RM) $(CLIENT_DOCKER_DIR)/test-framework/$(DW_CREDFILE)
	$(RM) $(CLIENT_DOCKER_DIR)/test-override/$(DW_CREDFILE)
endif

clean-dirs:
ifdef OUTPUT_DIR
	sudo $(RM_R) $(OUTPUT_DIR)
endif
ifdef INIT_DATA_DIR
	sudo $(RM_R) $(INIT_DATA_DIR)
endif
