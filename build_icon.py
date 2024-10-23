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

class update_general_and_system_flags:
    def __init__(self, config, ma_config):
        self._config = config['build-config']
        self._ma_config = ma_config['build-config']
        print(self._ma_config)
        print(self._config)

    def update(self, flag, subs):
        general = self._config[flag].format(**subs)
        system = self._ma_config[flag].format(**subs)

        subs[flag] = general + ' ' + system

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

    parser = argparse.ArgumentParser(description='Takes a YAML file with the configuration of ICON and runs the compilation')
    parser.add_argument('file_name', type=str, help="YAML file containing the parameters for the build configuration")
    parser.add_argument('--micro', type=str, help="YAML file containing the parameters for microarchitecture specific flags")
    parser.add_argument('--target', type=str, help="Target atchitecture. This flag will override the target entry in the yaml build configuration. It has to be an entry in the --micro <file> target identifyier")
    parser.add_argument('--conf', action='store_true', help="Ask to not only print the configure command but also run it")
    parser.add_argument('--make', action='store_true', help="Ask to run the make commands to build the application. It requires --conf to be specified")
    parser.add_argument('--prefix', help="Common prefix where all the relative paths in the 'paths' section of the yaml configuraiton file refers to. If left blank those paths will be considered as absolute")
    args = parser.parse_args()

    if not os.path.isfile(args.file_name):
        raise Exception("Main configuration file " + args.file_name + " not found, please check the path")
    
    if not os.path.isfile(args.micro):
        raise Exception("Microarchitecture configuration file " + args.micro + " not found, please check the path")

    print('Opening file ', args.file_name)
    config = read_config(args.file_name)

    print('Opening microarchitecture file ', args.micro)
    ma_config = read_config(args.micro)

    if config['uenv']['view'] != uenv_view:
        print('Warning: the view for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-view'], uenv_view))

    if config['uenv']['image'] != uenv_image:
        print('Warning: the image for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-image'], uenv_image))

    if ma_config['uenv']['view'] != uenv_view:
        print('Warning: the view for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-view'], uenv_view))

    if ma_config['uenv']['image'] != uenv_image:
        print('Warning: the image for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-image'], uenv_image))

    ma_target = config['target'] if args.target is None else args.target

    print("TARGET SPECIFIED:", ma_target)

    pwd = os.popen('pwd').read()
    common_prefix = args.prefix

    subs = {'uenv_root':uenv_root, 
            'icon_folder': os.path.join(common_prefix, config['paths'].get('icon_folder', pwd + '/icon-exclaim'))
    }

    check_package_path('icon4py', config, subs, common_prefix)
    check_package_path('gt4py', config, subs, common_prefix)
    check_package_path('gridtools_cpp', config, subs, common_prefix)

    # Setting up the paths to the icon4py modeules. Arguably these should not be specified here, sicne icon4py should know how to build stuff
    subs['icon4py_dycore'] =  os.path.join(subs['icon4py'], 'model/atmosphere/dycore/src/icon4py/model/atmosphere/dycore/')
    subs['icon4py_diffusion'] =  os.path.join(subs['icon4py'], 'model/atmosphere/diffusion/src/icon4py/model/atmosphere/diffusion/stencils')
    subs['icon4py_advection'] =  os.path.join(subs['icon4py'], 'model/atmosphere/advection/src/icon4py/model/atmosphere/advection/')
    subs['icon4py_interpolation'] =  os.path.join(subs['icon4py'], 'model/common/src/icon4py/model/common/interpolation/stencils')
    subs['icon4py_tools'] =  os.path.join(subs['icon4py'], 'tools/src/icon4pytools')
    subs['venv'] = venv_path

    subs['CXX'] = ma_config[ma_target]['compilers'].get('CXX', 'mpicxx')
    subs['FC'] = ma_config[ma_target]['compilers'].get('FC', 'mpif90')
    subs['CC'] = ma_config[ma_target]['compilers'].get('CC', 'mpicc')

    subs['cudaarch'] = ma_config[ma_target].get('cudaarch', 'CRAPPPP')

    ## Loading general settings
    ugsf = update_general_and_system_flags(config, ma_config[ma_target])
    ugsf.update('CONFIGURE_FLAGS', subs)
    ugsf.update('LIBS', subs)
    ugsf.update('FCFLAGS', subs)
    ugsf.update('LDFLAGS', subs)
    ugsf.update('CFLAGS', subs)
    ugsf.update('CPPFLAGS', subs)
    ugsf.update('GT4PYFLAGS', subs)
    ugsf.update('DSL_LDFLAGS', subs)

    # This is only available in system flags
    subs['NVCFLAGS'] = ma_config[ma_target]['build-config']['NVCFLAGS'].format(**subs)

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
        CMD_EXEC = r'''make -j4'''.format(**subs)
        os.system(CMD_EXEC)

if __name__=='__main__':
    config_and_build()
