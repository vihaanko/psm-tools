#!/bin/bash
cd openapi-generator
mvn clean install -U -DskipTests
cd ..

for file in ./swagger/*
do
  str1="${file/\.json/}"
  str2="${str1/\.\/swagger\//}"
  str3="${str2/\//}"
  str4="${str3/svc_/}"

  java -jar openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar generate -i "$file" -p group=$str4 -c genconfig.json -g python -o apigroups/$str4

  echo "$str4"
done