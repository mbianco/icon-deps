#!/bin/bash

THIS=`dirname $(realpath $0) `

print_usage() {
	echo "Usage:"
	echo "$0 --perfix <path> | --help"
	echo
	echo "This command will build all the recipes in specs/build-configs one after the other"
	echo
	echo "--prefix <path>, where path is the path to the folder containing the directories fo the software sources"
	echo
}

while [[ $# -gt 0 ]]; do
	case $1 in
        -p|--prefix)
            EXTENSION="$2"
            shift # past argument
            shift # past value
            ;;
        -h|--help)
            print_usage
			exit 0
            ;;
        -*|--*)
            echo "Unknown option $1"
			print_usage
            exit 1
            ;;
        *)
		  echo "Unrecognized option $1"
		  print_usage
		  exit 1
          ;;
    esac
done

for test in `ls $THIS/../specs/build-configs`; do
	echo $test
    python $THIS/../build_icon.py $THIS/../specs/build-configs/$test --prefix=$1 --micro=$THIS/../specs/architectures/microarchitecture.yaml --conf --make
	strip bin/icon
	mv bin/icon bin/`basename $test .yaml`
done
