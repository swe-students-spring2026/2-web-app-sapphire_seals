#!/bin/bash

source ../.env

wget -q -O bootstrap.zip https://big.hash.ooo/software-engineering/bootstrap.zip
unzip -o bootstrap.zip # contains all the json, prepared via dbutils.py

function import_collection {
  local collection=$1
  docker cp $collection.json mongodb:/$collection.json
  docker exec mongodb mongoimport -d $MONGO_DBNAME -c $collection --authenticationDatabase admin --collection $collection --username $MONGO_INITDB_ROOT_USERNAME --password $MONGO_INITDB_ROOT_PASSWORD --type json --jsonArray --file /$collection.json
}

import_collection "halls"
import_collection "menus"
import_collection "foods"
import_collection "tags"