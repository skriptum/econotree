#!/bin/bash
export DATABASE_URL=postgres://postgres:test123@localhost/django_db
export REDIS_URL=redis://localhost:6379
export OTREE_ADMIN_PASSWORD="test123"
export OTREE_PRODUCTION="1"
export OTREE_AUTH_LEVEL="STUDY"
sudo -E env "PATH=$PATH" otree prodserver 8001