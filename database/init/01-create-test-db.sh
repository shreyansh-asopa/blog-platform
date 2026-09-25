#!/bin/sh
# Creates the test database alongside the main one, owned by the same user.
set -e

if [ -n "$POSTGRES_TEST_DB" ]; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE "$POSTGRES_TEST_DB" OWNER "$POSTGRES_USER";
EOSQL
fi
