# Python Yaml Icon Build

import yaml
import argparse
import os

def get_yaml_config(file):
    with open(file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def config_and_build():
    uenv_root = os.environ.get('UENV_MOUNT_POINT', 'not_set')
    parser = argparse.ArgumentParser(description='Takes a YAML file with the configuration of ICON and runs the compilation')
    parser.add_argument('file_name', type=str, help="YAML file containing the parameters for the configuration")
    args = parser.parse_args()

    print('Opening file ', args.file_name)
    config = get_yaml_config(args.file_name)

    print(config)
    print(config['paths'])

    pwd = os.popen('pwd').read()

    subs = {'uenv_root':uenv_root, 
            'icon_folder':config['paths'].get('icon_folder', pwd + '/icon-exclaim'),
            'gt4py': config['paths'].get('gt4py', pwd + '/gt4py'),
            'icon4py': config['paths'].get('icon4py', pwd + 'icon4py'),
            'gridtools': config['paths'].get('gridtools', pwd + '/gridtools')}

    subs['icon4py_dycore'] = config['icon4py_modules'].get('dycore', subs['icon4py'] + '/model/atmosphere/dycore/')
    subs['icon4py_advection'] = config['icon4py_modules'].get('advection', subs['icon4py'] + '/model/atmosphere/advection')
    subs['icon4py_diffusion'] = config['icon4py_modules'].get('diffusion', subs['icon4py'] + '/model/atmosphere/diffusion/stencils')
    subs['icon4py_interpolation'] = config['icon4py_modules'].get('interpolation', subs['icon4py'] + '/model/common/interpolation/stencils')
    subs['icon4py_tools'] = config['icon4py_modules'].get('tools', subs['icon4py'] + '/tools/src/icon4pytools')
    subs['venv'] = config['paths'].get('venv', subs['icon4py'] + '/.venv')

    subs['additionalCFLAGS'] = config['system'].get('CFLAGS', '')
    subs['CXX'] = config['system'].get('CXX', 'mpicxx')
    subs['FC'] = config['system'].get('FC', 'mpif90')
    subs['CC'] = config['system'].get('CC', 'mpicc')
    subs['cudaarch'] = config['system'].get('cudaarch', '80')

    CMD = '''{icon_folder}/configure \ 
              CC="{CC}" \ 
              CFLAGS="-g -O2 {additionalCFLAGS}" \ 
              CPPFLAGS="-I{uenv_root}/include -I{uenv_root}/include/libxml2" \ 
              CXX="{CXX}" \ 
              FC="{FC}" \ 
              CUDAARCHS="{cudaarch}" \ 
              NVCFLAGS="-ccbin nvc++ -g -O3 -arch=sm_{cudaarch}" \ 
              FCFLAGS="-g -traceback -O -Mrecursive -Mallocatable=03 -Mbackslash -Mstack_arrays -acc=verystrict -gpu=cc{cudaarch} -Minfo=accel,inline ${{SERIALBOXI}} ${{ECCODESI}} ${{NETCDFFI}} -D__USE_G2G -D__SWAPDIM" \ 
              LDFLAGS="-L${uenv_root}/lib64 -L${uenv_root}/lib" \ 
              DSL_LDFLAGS="-L${uenv_root}/lib64 -L${uenv_root}/lib" \ 
              LIBS="-lcudart -Wl,--as-needed -lxml2 -llapack -lblas ${{SERIALBOX2_LIBS}} -lc++libs -lnetcdf -lnetcdff -nvmalloc" \ 
              MPI_LAUNCH=false \ 
              GT4PYNVCFLAGS="$GT4PYNVCFLAGS" \ 
              SB2PP="$SB2PP" \ 
              LOC_GT4PY={gt4py} \ 
              LOC_ICON4PY_ATM_DYN_ICONAM={icon4py_dycore} \ 
              LOC_ICON4PY_ADVECTION={icon4py_advection} \ 
              LOC_ICON4PY_DIFFUSION={icon4py_diffusion} \ 
              LOC_ICON4PY_INTERPOLATION={icon4py_interpolation} \ 
              LOC_ICON4PY_TOOLS={icon4py_tools} \ 
              LOC_ICON4PY_BIN={venv} \ 
              LOC_GRIDTOOLS={gridtools} \ 
              ${{EXTRA_CONFIG_ARGS}} --disable-rte-rrtmgp --enable-liskov=substitute --disable-liskov-fused'''.format(**subs)

    os.system(CMD)

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

    print(CMD)

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

