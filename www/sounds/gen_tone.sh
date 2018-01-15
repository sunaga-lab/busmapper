#!/bin/bash

cd `dirname $0`

for oct in 1 2 3 4 5 6; do
    for key in C D E F G A B; do
        FILENAME="tone-sin-${key}${oct}-fo.mp3"
        echo "Generating $FILENAME"
        sox -n ${FILENAME} synth 0.4 sine ${key}${oct} fade t 0 0 0:0.4
    done
done

