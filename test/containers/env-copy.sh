#!/bin/bash

trim () {
    var=$1
    var="${var#"${var%%[![:space:]]*}"}"
    var="${var%"${var##*[![:space:]]}"}"
    echo $var
}

declare -A current_values
filename='env.default'

if test -e ${filename}
then
    while read -r line
    do
        if [[ ${line} =~ "=" ]]
        then
            IFS='=' read -ra values <<< $line
            key="$(trim ${values[0]})"
            value="$(trim ${values[1]})"
            current_values[$key]=$value
        else
            :
        fi
    done < ${filename}
fi

for key in "${!current_values[@]}"
do
  echo "Key is '$key'  => Value is '${current_values[$key]}'"
done
