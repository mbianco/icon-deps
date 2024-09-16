# icon-deps
building icon dependencies for icon[-dsl]


usage: YIB.py [-h] [--conf] [--make] file_name

Takes a YAML file with the configuration of ICON and runs the compilation

positional arguments:
  file_name   YAML file containing the parameters for the configuration

options:
  -h, --help  show this help message and exit
  --conf      Ask to not only print the configure command but also run it
  --make      Ask to run the make commands to build the application. It requires --conf to be specified

  
