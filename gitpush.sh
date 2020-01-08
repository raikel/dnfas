#!/usr/bin/env bash

MSG="Project updated"

if [[ "$1" != "" ]]; then
    MSG=${1}
fi


git add .
git status
git commit -m "${MSG}"
git push origin master