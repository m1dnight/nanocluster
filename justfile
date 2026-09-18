set positional-arguments := true

# List available commands.
default:
    @just --list

# Install Ansible role and collection dependencies on this machine.
deps:
    ansible-galaxy install -r requirements.yml

# Set up packages, Go, asdf, Erlang, and Elixir on all active nodes.
setup *args:
    ansible-playbook pb_setup.yml "$@"

# Configure Pi 1's fan; pass -e fan_controller_speed=50 to set its duty cycle.
fan_speed *args:
    ansible-playbook pb_fan_speed.yml "$@"

# Add the configured SSH public key to selected accounts on all active nodes.
ssh_keys *args:
    ansible-playbook pb_ssh_keys.yml "$@"

# Write the shared Erlang cookie to the configured user's home on every node.
erlang_cookie *args:
    ansible-playbook pb_erlang_cookie.yml "$@"
