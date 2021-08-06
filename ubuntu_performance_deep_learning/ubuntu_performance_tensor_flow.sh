#!/usr/bin/env bash
#
# perform TensorFlow performance testing and corresponding pre-setup.
#

set -eo pipefail

CONTAINER_VER="21.07"

install_nvidia_docker() {
    local distribution
    distribution="$(. /etc/os-release;echo $ID$VERSION_ID)"
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
        sudo tee /etc/apt/sources.list.d/nvidia-docker.list > /dev/null
    sudo apt update
    sudo apt install nvidia-docker2 -y
    sudo systemctl restart docker
}

get_num_gpus() {
    # required to passthrough GPUs into containers
    nvidia-smi -L | wc -l
}

setup() {
    # pre-setup testing environment and necessary tools
    install_nvidia_docker
}

run_test() {
    sudo nvidia-docker run \
         --shm-size=1g \
         --ulimit memlock=-1 \
         --ulimit stack=67108864 \
         --rm nvcr.io/nvidia/tensorflow:${CONTAINER_VER}-tf1-py3 -- \
         mpiexec \
         --bind-to socket \
         --allow-run-as-root \
         -np "$(get_num_gpus)" \
         python -u /workspace/nvidia-examples/cnn/resnet.py \
         --layers=50 \
         --precision=fp16 \
         --batch_size=256 \
         --num_iter=300 \
         --iter_unit=batch \
         --display_every=300
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
