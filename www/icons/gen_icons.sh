#!/usr/bin/env bash

declare -A COLORS
COLORS=(
  ["red"]="rgb(204,0,0)"
  ["green"]="rgb(0,204,0)"
  ["blue"]="rgb(0,0,204)"
  ["cyan"]="rgb(0,204,204)"
  ["purple"]="rgb(204,0,204)"
  ["yellow"]="rgb(204,204,0)"
)
echo "enum: ${!COLORS[@]}"

for color in ${!COLORS[@]}; do
  colorval=${COLORS[$color]}
  echo "Color: $color val=$colorval"

  sed -e "s/rgb(0,204,0)/$colorval/g" bus-icon.svg > bus-icon-${color}.svg

  rsvg-convert -w 100 -h 100 "bus-icon-${color}.svg" --format=png --output=bus-icon-${color}.png
  #convert -density 120 -background black bus-icon-${color}.svg -resize 100x100 bus-icon-${color}.png

done





