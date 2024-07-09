# Python Yaml Icon Build

import yaml
from jsonschema import validate
import argparse
import os

def read_config(file):
    with open(file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def update_general_and_system_flags(flag, config, subs):
    general = config['general'][flag].format(**subs)
    system = config['system'][flag].format(**subs)

    subs[flag] = general + ' ' + system


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
    print("----------------------------------------")
    print(args)
    print("----------------------------------------")


    print('Opening file ', args.file_name)
    config = read_config(args.file_name)
    print(config)
    print(config['paths'])

    if config['uenv-view'] != uenv_view:
        print('Warning: the view for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-view'], uenv_view))

    if config['uenv-image'] != uenv_image:
        print('Warning: the image for which the configuration is done is {0}, while the environment view is {1}'.format(config['uenv-image'], uenv_image))

    pwd = os.popen('pwd').read()

    subs = {'uenv_root':uenv_root, 
            'icon_folder':config['paths'].get('icon_folder', pwd + '/icon-exclaim'),
            'gt4py': config['paths'].get('gt4py', pwd + '/gt4py'),
            'icon4py': config['paths'].get('icon4py', pwd + '/icon4py'),
            'gridtools': config['paths'].get('gridtools', pwd + '/gridtools')}

    subs['icon4py_dycore'] = config['icon4py_modules'].get('dycore', subs['icon4py'] + '/model/atmosphere/dycore/').format(**subs)
    subs['icon4py_advection'] = config['icon4py_modules'].get('advection', subs['icon4py'] + '/model/atmosphere/advection').format(**subs)
    subs['icon4py_diffusion'] = config['icon4py_modules'].get('diffusion', subs['icon4py'] + '/model/atmosphere/diffusion/stencils').format(**subs)
    subs['icon4py_interpolation'] = config['icon4py_modules'].get('interpolation', subs['icon4py'] + '/model/common/interpolation/stencils').format(**subs)
    subs['icon4py_tools'] = config['icon4py_modules'].get('tools', subs['icon4py'] + '/tools/src/icon4pytools').format(**subs)
    subs['venv'] = config['paths'].get('venv', subs['icon4py'] + '/.venv').format(**subs)

    subs['CXX'] = config['paths'].get('CXX', 'mpicxx')
    subs['FC'] = config['paths'].get('FC', 'mpif90')
    subs['CC'] = config['paths'].get('CC', 'mpicc')

    subs['cudaarch'] = config['system'].get('cudaarch', '80')

    ## Loading general settings
    update_general_and_system_flags('LIBS', config, subs)
    update_general_and_system_flags('FCFLAGS', config, subs)
    update_general_and_system_flags('LDFLAGS', config, subs)
    update_general_and_system_flags('CFLAGS', config, subs)
    update_general_and_system_flags('CPPFLAGS', config, subs)
    update_general_and_system_flags('GT4PYFLAGS', config, subs)
    update_general_and_system_flags('DSL_LDFLAGS', config, subs)
    # This is only available in system flags
    subs['NVCFLAGS'] = config['system']['NVCFLAGS'].format(**subs)

    subs['CONFIGURE_FLAGS'] = config['general']['CONFIGURE_FLAGS'].format(**subs)

    os.system('mpif90 --version; ls -l {uenv_root}; uenv status;'.format(**subs))

    CMD = r'''{icon_folder}/configure \
              FCFLAGS="{FCFLAGS}" \
              CC="{CC}" \
              CFLAGS="{CFLAGS}" \
              CPPFLAGS="{CPPFLAGS}" \
              CXX="{CXX}" \
              FC="{FC}" \
              CUDAARCHS="{cudaarch}" \
              NVCFLAGS="{NVCFLAGS}" \
              LDFLAGS="{LDFLAGS}" \
              DSL_LDFLAGS="{DSL_LDFLAGS}" \
              LIBS="{LIBS}" \
              MPI_LAUNCH=false \
              GT4PYNVCFLAGS="{GT4PYFLAGS}" \
              SB2PP="$SB2PP" \
              LOC_GT4PY={gt4py} \
              LOC_ICON4PY_ATM_DYN_ICONAM={icon4py_dycore} \
              LOC_ICON4PY_ADVECTION={icon4py_advection} \
              LOC_ICON4PY_DIFFUSION={icon4py_diffusion} \
              LOC_ICON4PY_INTERPOLATION={icon4py_interpolation} \
              LOC_ICON4PY_TOOLS={icon4py_tools} \
              LOC_ICON4PY_BIN={venv} \
              LOC_GRIDTOOLS={gridtools} \
              {CONFIGURE_FLAGS}
            '''.format(**subs)

    print(CMD)
    
    if args.conf:
        os.system(CMD)

    if args.conf and args.make:
        CMD_EXEC = r'''make -j2
            ./make_runscripts --all'''.format(**subs)
    
              #for arg in "$@"; do
              #  case $arg in
              #    -help | --help | --hel | --he | -h | -help=r* | --help=r* | --hel=r* | --he=r* | -hr* | -help=s* | --help=s* | --hel=s* | --he=s* | -hs*)
              #       test -n "${{EXTRA_CONFIG_ARGS}}" && echo '' && echo "This wrapper script ('$0') calls the configure script with the following extra arguments, which might override the default values listed above: ${{EXTRA_CONFIG_ARGS}}"
              #       exit 0 ;;
              #  esac
              #done

              ## Copy runscript-related files when building out-of-source:
              #if test $(pwd) != $(cd "{icon_folder}"; pwd); then
              #  echo "Copying runscript input files from the source directory..."
              #  rsync -uavz {icon_folder}/run . --exclude='*.in' --exclude='.*' --exclude='standard_*'
              #  ln -sf -t run/ {icon_folder}/run/standard_*
              #  rsync -uavz {icon_folder}/externals . --exclude='.git' --exclude='*.f90' --exclude='*.F90' --exclude='*.c' --exclude='*.h' --exclude='*.Po' --exclude='tests' --exclude='*.mod' --exclude='*.o'
              #  rsync -uavz {icon_folder}/make_runscripts .
              #  ln -sf {icon_folder}/data
              #  ln -sf {icon_folder}/vertical_coord_tables
              #fi'''.format(**subs)


    #os.system('mkdir -p build_substitution4')
    #cmd = '''pushd build_substitution4; 
    #    NETCDFMINFORTRAN={uenv_root} 
    #    NETCDF={uenv_root} 
    #    XML2_ROOT={uenv_root} 
    #    LOC_GT4PY={gt4py} 
    #    LOC_ICON4PY_ATM_DYN_ICONAM={icon4py_dycore} 
    #    LOC_ICON4PY_ADVECTION={icon4py_advection}
    #    LOC_ICON4PY_DIFFUSION={icon4py_diffusion}
    #    LOC_ICON4PY_INTERPOLATION={icon4py_interpolation}
    #    LOC_ICON4PY_TOOLS={icon4py_tools}
    #    LOC_ICON4PY_BIN={venv}
    #    LOC_GRIDTOOLS={gridtools}
    #    ../{icon_folder}/config/cscs/santis_nospack.dsl.nvidia_v4 --disable-rte-rrtmgp --enable-liskov=substitute --disable-liskov-fused
    #
    #    #make
    #    make -j20
    #    ./make_runscripts --all
    #    #pushd run
    #    #    sbatch exp.exclaim_ape_R02B05_alpsbench.run
    #    #popd
    #popd'''.format(**subs)
    #print(cmd)
    #os.system(cmd)

if __name__=='__main__':
    config_and_build()

