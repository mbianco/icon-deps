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

def update_general_and_system_flags(flag, config, subs):
    general = config['general'][flag].format(**subs)
    system = config['system'][flag].format(**subs)

    subs[flag] = general + ' ' + system

def check_package_path(package, config, subs):
    print("Looking for " + package + "...")
    common_prefix = config['paths'].get('common_prefix', '')
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
    uenv_image = os.environ.get('UENV_VIEW', 'not_set').split(':')[1]
    uenv_root = os.environ.get('UENV_MOUNT_POINT', 'not_set')+'/env/'+uenv_view
    #print('uenv_view', uenv_view)

    parser = argparse.ArgumentParser(description='Takes a YAML file with the configuration of ICON and runs the compilation')
    parser.add_argument('file_name', type=str, help="YAML file containing the parameters for the configuration")
    parser.add_argument('--conf', action='store_true', help="Ask to not only print the configure command but also run it")
    parser.add_argument('--make', action='store_true', help="Ask to run the make commands to build the application. It requires --conf to be specified")
    args = parser.parse_args()

    print('Opening file ', args.file_name)
    config = read_config(args.file_name)

    if config['uenv-view'] != uenv_view:
        print('Warning: the view for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-view'], uenv_view))

    if config['uenv-image'] != uenv_image:
        print('Warning: the image for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-image'], uenv_image))

    pwd = os.popen('pwd').read()
    common_prefix = config['paths'].get('common_prefix', '')
    subs = {'uenv_root':uenv_root, 
            'icon_folder': os.path.join(common_prefix, config['paths'].get('icon_folder', pwd + '/icon-exclaim'))
    }


    check_package_path('icon4py', config, subs)
    check_package_path('gt4py', config, subs)
    check_package_path('gridtools_cpp', config, subs)

    subs['icon4py_dycore'] =  os.path.join(subs['icon4py'], config['icon4py_modules'].get('dycore', 'DEFAULTmodel/atmosphere/dycore/src/icon4py/model/atmosphere/dycore/').format(**subs))
    subs['icon4py_advection'] =  os.path.join(subs['icon4py'], config['icon4py_modules'].get('advection', 'DEFAULTmodel/atmosphere/advection/src/icon4py/model/atmosphere/advection/').format(**subs))
    subs['icon4py_diffusion'] =  os.path.join(subs['icon4py'], config['icon4py_modules'].get('diffusion', 'DEFAULT/model/atmosphere/diffusion/src/icon4py/model/atmosphere/diffusion/stencils').format(**subs))
    subs['icon4py_interpolation'] =  os.path.join(subs['icon4py'], config['icon4py_modules'].get('interpolation', 'DEFAULT/model/common/src/icon4py/model/common/interpolation/stencils').format(**subs))
    subs['icon4py_tools'] =  os.path.join(subs['icon4py'], config['icon4py_modules'].get('tools', 'DEFAULT/tools/src/icon4pytools').format(**subs))
    subs['venv'] =  os.path.join(subs['icon4py'], config['paths'].get('venv', subs['icon4py'] + '/.venv').format(**subs))

    subs['CXX'] = config['compilers'].get('CXX', 'mpicxx')
    subs['FC'] = config['compilers'].get('FC', 'mpif90')
    subs['CC'] = config['compilers'].get('CC', 'mpicc')

    subs['cudaarch'] = config['system'].get('cudaarch', '80')

    ## Loading general settings
    update_general_and_system_flags('LIBS', config, subs)
    update_general_and_system_flags('FCFLAGS', config, subs)
    update_general_and_system_flags('LDFLAGS', config, subs)
    update_general_and_system_flags('CFLAGS', config, subs)
    update_general_and_system_flags('CPPFLAGS', config, subs)
    update_general_and_system_flags('GT4PYFLAGS', config, subs)
    update_general_and_system_flags('DSL_LDFLAGS', config, subs)
    update_general_and_system_flags('CONFIGURE_FLAGS', config, subs)

    # This is only available in system flags
    subs['NVCFLAGS'] = config['system']['NVCFLAGS'].format(**subs)

    CMD = r'''{icon_folder}/configure \
              FCFLAGS="{FCFLAGS}" \
              CC="{CC}" \
              CFLAGS="{CFLAGS}" \
              CPPFLAGS="{CPPFLAGS}" \
              CXX="{CXX}" \
              FC="{FC}" \
              CUDAARCH="{cudaarch}" \
              NVCFLAGS="{NVCFLAGS}" \
              LDFLAGS="{LDFLAGS}" \
              DSL_LDFLAGS="{DSL_LDFLAGS}" \
              LIBS="{LIBS}" \
              MPI_LAUNCH=true \
              GT4PYNVCFLAGS="{GT4PYFLAGS}" \
              SB2PP="$SB2PP" \
              LOC_GT4PY={gt4py} \
              LOC_ICON4PY_ATM_DYN_ICONAM={icon4py_dycore} \
              LOC_ICON4PY_ADVECTION={icon4py_advection} \
              LOC_ICON4PY_DIFFUSION={icon4py_diffusion} \
              LOC_ICON4PY_INTERPOLATION={icon4py_interpolation} \
              LOC_ICON4PY_TOOLS={icon4py_tools} \
              LOC_ICON4PY_BIN={venv} \
              LOC_GRIDTOOLS={gridtools_cpp} \
              {CONFIGURE_FLAGS}
            '''.format(**subs)

    print(CMD)
    
    if args.conf:
        os.system(CMD)

    if args.conf and args.make:
        CMD_EXEC = r'''make -j2'''.format(**subs)
        os.system(CMD_EXEC)

if __name__=='__main__':
    config_and_build()

