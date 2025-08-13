#!/bin/bash -i

# Change to the directory where this script is located
cd "$(dirname "$0")"

cd clustertest

mix local.hex --force
mix local.rebar --force
# which iex
# which mix
mix release --overwrite

export RELEASE_COOKIE=secret

pkill -f clustertest
_build/dev/rel/clustertest/bin/clustertest stop
_build/dev/rel/clustertest/bin/clustertest daemon
