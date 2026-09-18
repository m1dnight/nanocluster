set positional-arguments := true

# List available commands.
default:
    @just --list

# Install the Ansible role dependency on this machine.
deps:
    ansible-galaxy role install -r collections/requirements.yml

# Set up packages, Go, asdf, Erlang, and Elixir on all active nodes.
setup *args:
    ansible-playbook setup.yml "$@"

# Configure Pi 1's fan; pass -e fan_controller_speed=50 to set its duty cycle.
fan_speed *args:
    ansible-playbook fan_speed.yml "$@"
