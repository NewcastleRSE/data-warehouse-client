#!/bin/bash

source .env

echo "{
    \"user\" : \"${POSTGRES_USER}\",
    \"pass\" : \"${POSTGRES_PASSWORD}\",
    \"IP\"   : \"pgdb\",
    \"port\" : \"${POSTGRES_PORT}\"
}" > ${DW_CREDFILE}

