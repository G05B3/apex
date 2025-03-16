# APEX
## An Automated Processing Element Creator

A tool that automatically generates the verilog code for the desired Processing Element (PE) architecture. Includes a graphical user interface where users can instantiate several basic components and connect them, in an intuitive manner. The available components are:
- 32 bit Inputs
- 32 bit Outputs
- Multiplexers (size generated automatically)
- Functional Units (with several possible operations)
- 32 bit Registers

The tool also generates an intermediate representation of the architecture through a .json file.

# Build
To build the tool, just run the following command:
> make

# Run
To run the tool, you can run either:
> python3 apex.py
or
> python3 pe-creator.py
> ./apex_vgen <name of the json file>
