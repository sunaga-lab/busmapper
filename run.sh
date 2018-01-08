#!/bin/bash


./parse.py > prolog/db.pl

swipl -f prolog/busmapper.pl


