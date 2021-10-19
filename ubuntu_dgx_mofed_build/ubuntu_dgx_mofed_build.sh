#!/usr/bin/env bash
#
# perform mlnx testing and corresponding pre-setup.
#

set -eo pipefail

setup() {
    # pre-setup testing environment and necessary tools
    # currently there is nothing practically but will be used possibly in the future.
    echo "begin to pre-setup mlnx testing"
}

run_test() {
    exe_dir=$(dirname "${BASH_SOURCE[0]}")
    pushd ${exe_dir}
    ./check-mofed-modules.sh
    popd
}

case $1 in
    setup)
        echo ""
        echo "On setting up necessary test environment..."
        echo ""
        setup
        echo ""
        echo "Setting up necessary test environment..."
        echo ""
        ;;
    test)
        echo ""
        echo "On running test..."
        echo ""
        run_test
        echo ""
        echo "Running test..."
        echo ""
        ;;
esac
