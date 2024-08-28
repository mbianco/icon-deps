#!/bin/bash
set -e

SCRIPT_PATH=`dirname $0`

_setup_trace_output() {
  trap '[[ "$BASH_COMMAND" == *"echo"* ]] || echo \$ $BASH_COMMAND' DEBUG
};

# Function to parse branch and org from an argument
parse_branch_and_org() {
    local arg=$1
    local var_name=$2

    if [[ $arg == *"/"* ]]; then
        eval "${var_name}_org=\"${arg%%/*}\""
        eval "${var_name}_branch=\"${arg#*/}\""
    else
        eval "${var_name}_branch=\"$arg\""
    fi
}

# Default branches if not provided
icon_branch="icon-dsl"
icon4py_branch="main"
gt4py_branch="main"
gridtools_branch="master"

# Default organizations
icon_org="C2SM"
icon4py_org="C2SM"
gt4py_org="GridTools"
gridtools_org="GridTools"

# Help string
print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Clones and sets up repositories for ICON model, ICON4py, GT4py, and GridTools."
    echo
    echo "Options:"
    echo "  --icon <branch>|<org>/<branch>      Set the branch (and organization) for ICON repository. Default: $icon_org/$icon_branch"
    echo "  --icon4py <branch>|<org>/<branch>   Set the branch (and organization) for ICON4py repository. Default: $icon4py_org/$icon4py_branch"
    echo "  --gt4py <branch>|<org>/<branch>     Set the branch (and organization) for GT4py repository. Default: $gt4py_org/$gt4py_branch"
    echo "  --gridtools <branch>|<org>/<branch> Set the branch (and organization) for GridTools repository. Default: $gridtools_org/$gridtools_branch"
    echo ""
    echo "Example:"
    echo "  ./install_dependencies.sh"
    echo "  ./install_dependencies.sh --icon icon-dsl --gt4py your_fork/your_branch"
}


# Parse arguments
while [ "$1" != "" ]; do
    case $1 in
        --icon )       shift
                       parse_branch_and_org "$1" "icon"
                       ;;
        --icon4py )    shift
                       parse_branch_and_org "$1" "icon4py"
                       ;;
        --gt4py )      shift
                       parse_branch_and_org "$1" "gt4py"
                       ;;
        --gridtools )  shift
                       parse_branch_and_org "$1" "gridtools"
                       ;;
        --help )       print_help
                       exit 0
                       ;;
        * )            echo "Invalid option"
                       print_help
                       exit 1
    esac
    shift
done

# Enable debug mode
set -x

# core dependencies
#source ${SCRIPT_PATH}/env.sh

# Assemble urls
icon_url="git@github.com:${icon_org}/icon-exclaim.git"
icon4py_url="git@github.com:${icon4py_org}/icon4py.git"
gt4py_url="git@github.com:${gt4py_org}/gt4py.git"
gridtools_url="git@github.com:${gridtools_org}/gridtools.git"

# Clone with specific branches
#git clone -b $icon_branch $icon_url
#git clone -b $icon4py_branch $icon4py_url

export CXX=`which g++`
g++ --version
export CC=`which gcc`
gcc --version

pushd icon4py
    python3.10 -m venv .venv
    source .venv/bin/activate
    export CPATH=/user-environment/env/icon/include
    export C_INCLUDE_PATH=/user-environment/env/icon/include
    export CPLUS_INCLUDE_PATH=/user-environment/env/icon/include
    pip install --upgrade wheel pip
    pip cache purge
    pip install --global-option="-I/user-environment/env/icon/include/" h5py
    pip install  -r requirements-dev.txt
    #pip install --config-settings='--build-option="-I/user-environment/env/icon/include/"' -r requirements-dev.txt
popd


deactivate

