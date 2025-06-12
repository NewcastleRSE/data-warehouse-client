#!/bin/bash

DEBUG=

###############################################################################
# Trim leading and trainling whitespace
###############################################################################
trim () {
    var=$1
    var="${var#"${var%%[![:space:]]*}"}"
    var="${var%"${var##*[![:space:]]}"}"
    echo $var
}

###############################################################################
# Read and process user environment values, if they exist
###############################################################################
declare -A usr_env

filename='.env'
if test -e ${filename}
then
    while read -r line
    do
        # Comments (otherwise a "=" sign in a comment will trigger a match)
        if [[ ${line} =~ "#" ]]
        then
            continue
        fi

        # Blank lines
        if test -z $(trim ${line}) 
        then
            continue
        fi

        # Variable definitions
        if [[ ${line} =~ "=" ]]
        then
            IFS='=' read -ra vals <<< $line
            key="$(trim ${vals[0]})"
            val="$(trim ${vals[1]})"
            usr_env[$key]=$val
        else
            :
        fi
    done < $filename
fi

if test ! -z $DEBUG
then
    for key in "${!usr_env[@]}"
    do
        echo "Key is '$key'  => Value is '${usr_env[$key]}'"
    done
fi

###############################################################################
# Read the defaults file, overriding default values with pre-existing ones
###############################################################################
filename='.env.default'
buffer=''
if test -e $filename
then
    while read -r line
    do
        if [[ ${line} =~ "=" ]]
        then
            IFS='=' read -ra vals <<< $line
            key="$(trim ${vals[0]})"
            val="$(trim ${vals[1]})"
            if test ! -z ${usr_env[$key]}
            then
                if test ${usr_env[$key]} != ${val}
                then
                    line=$(echo "${line}" | sed "s/${val}/${usr_env[$key]}/g")
                fi
            fi
        fi
        buffer="${buffer}${line}\n"
    done < $filename
fi

printf "$buffer" > '.env'
printf "Wrote updated config file to [.env]\n"
