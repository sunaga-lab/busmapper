#!/bin/bash


build_tables.py > prolog/db.pl

swipl -f prolog/busmapper.pl


