#!/bin/bash -i

# Change to the directory where this script is located
cd "$(dirname "$0")"

# rm -rf connect-four
# git clone https://github.com/m1dnight/connect-four.git

mix local.hex --force
mix local.rebar --force
mix deps.get
mix compile
mix release --overwrite

export RELEASE_DISTRIBUTION=name
export RELEASE_COOKIE=secret
export RELEASE_NODE="app@$(hostname -f)"
pkill -f beam
/home/pi/sync/connect-four/_build/dev/rel/connect_four/bin/connect_four daemon
