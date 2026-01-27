#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Run the schema
sqlcmd -S "$DB_HOST,$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -P "$DB_PASSWORD" -i schema.sql