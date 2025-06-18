#!/bin/bash

DEBUG=

###############################################################################
# External functions
###############################################################################
source env-common.sh

###############################################################################
# Fields to create secrets for. Change "1" to "0" to prevent.
###############################################################################
declare -A sect_fields=(
    ["POSTGRES_PASSWORD"]="1"
    ["POSTGRES_SUPERUSER_PASSWORD"]="1"
)

###############################################################################
# Generate a random secret
###############################################################################
randsect1 () {
    head -c ${1-12} /dev/urandom | base64
}
randsect2 () {
    openssl rand -base64 12
}

###############################################################################
# Read and process env file
###############################################################################
filename='.env'
buffer=""
if test -e $filename
then
    while read -r line
    do
        # Skip comments (otherwise a "=" sign in a comment will match)
        if [[ ${line} =~ "#" ]]
        then
            buffer="${buffer}${line}\n"
            continue
        fi

        # Skip blank lines
        if test -z $(trim ${line}) 
        then
            buffer="${buffer}${line}\n"
            continue
        fi
        
        if [[ ${line} =~ "=" ]]
        then
            IFS='=' read -ra vals <<< $line
            key="$(trim ${vals[0]})"
            val="$(trim ${vals[1]})"
        fi

        if test "${sect_fields[$key]}" == "1"
        then
            # If key is specified as an argument do that one and ignore the rest
            if test ! -z $1
            then
                if test $1 != $key
                then
                    buffer="${buffer}${line}\n"
                    continue
                fi
            fi

            # Otherwise if this key is a placeholder, generate secret
            if test $val == "<placeholder>"
            then
                printf 'Generating secret %s\n' $key
                # Generated secrets can have "/" characters which need to be
                # escaped using the bash ${parameter//pattern/string} parameter
                # substitution rule, or sed will complain
                new_sect=$(randsect2)
                line=$(echo "${line}" | sed "s/${val}/${new_sect//\//\\/}/g")
            else
                printf 'Secret %s already set - skipping\n' $key
            fi
        fi
        buffer="${buffer}${line}\n"
    done < $filename

    printf "$buffer" > '.env'
    printf "Wrote updated config to [%s]\n" $filename
else
    printf "Environment file [%s] does not exist - no action taken\n" $filename
fi

