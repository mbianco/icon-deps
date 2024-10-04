# Python Yaml Icon Build

import yaml
from jsonschema import validate
import argparse
import os
import importlib.util

def read_config(file):
    with open(file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def check_package_path(package, config, subs, common_prefix):
    print("Looking for " + package + "...")
    package_from_config = config['paths'].get(package, "")
    if package_from_config == "":

        spec = importlib.util.find_spec(package)
        if spec is not None:
            package_from_config = os.path.join(os.path.dirname(spec.origin), 'data')
            print(package + " found automatically @ " + package_from_config)
        else:
            raise Exception(package + " not found, please check your configuraiton file")
    else:
        # Get a full path
        package_from_config = os.path.join(common_prefix, package_from_config)

    subs[package] = package_from_config

def config_and_build():
    uenv_view = os.environ.get('UENV_VIEW', 'not_set').split(':')[2]
    venv_path = os.environ.get('VIRTUAL_ENV', 'not_set')
    if venv_path == 'not_set':
        raise("ERROR: It is required to run these procedure from within a virtual environment")
    uenv_image = os.environ.get('UENV_VIEW', 'not_set').split(':')[1]
    uenv_root = os.environ.get('UENV_MOUNT_POINT', 'not_set')+'/env/'+uenv_view
    #print('uenv_view', uenv_view)

    parser = argparse.ArgumentParser(description='Takes a YAML file with list of packages to download and operate on them automatically')
    parser.add_argument('file_name', type=str, help="YAML file containing the parameters for the configuration")
    parser.add_argument('--prefix', help="Common prefix where all the relative paths in the 'paths' section of the yaml configuraiton file refers to. If left blank those paths will be considered as absolute")
    parser.add_argument('--dry', action='store_true', help="If set the operations will not be executed but simply printed on the screen")
    args = parser.parse_args()

    print('Opening file ', args.file_name)
    config = read_config(args.file_name)

    if config['uenv']['view'] != uenv_view:
        print('Warning: the view for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-view'], uenv_view))

    if config['uenv']['image'] != uenv_image:
        print('Warning: the image for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-image'], uenv_image))

    pwd = os.popen('pwd').read()
    common_prefix = args.prefix

    subs = {'uenv_root':uenv_root }

    for package_name in config['packages']:
        package = config['packages'][package_name]
        print("Checking package", package_name)
        if not os.path.isdir(package['folder']):

            cmd = "git clone " + package['git-url'] + '; popd'
            print(cmd)
            if not args.dry:
                os.system(cmd)

            cmd = 'pushd ' + package['folder'] + "; git checkout " + package['git-branch'] + '; popd'
            print(cmd)
            if not args.dry:
                os.system(cmd)

            cmd = 'pushd ' + package['folder'] + "; " + package['post-install'] + '; popd'
            print(cmd)
            if not args.dry:
                os.system(cmd)
        else:
            print("Skipping package " + package_name + " since folder already exists")
        
if __name__=='__main__':
    config_and_build()
