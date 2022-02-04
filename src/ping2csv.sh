#!/bin/bash
## Based on a post on stackoverflow:
## https://stackoverflow.com/questions/33720165/bash-ping-output-in-csv-format
## Changed to clean up and get it to work on Mac OS

declare site=''
declare result=''
declare prctg=''

site=$1
result="$site"

pingOutput=$(ping $site -c10 -i0.2 -q| tail -n2)

fl=true

while IFS= read -r line
do
    echo $line
    if [ "$fl" == "true" ]
    then
        prctg=$(echo "$line" | grep -Eo "[.[:digit:]]{1,10}%")
        result="$result $prctg"
        fl=false
    fi
    if [ "$prctg" == "100" ]
    then
        result="$result -1 -1 -1 -1"
    else
        result="$result $(echo "$line" | cut -d' ' -f4 | sed -E 's/\// /g')"
    fi
done <<< "$pingOutput"

echo "$result"
