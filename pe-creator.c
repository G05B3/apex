#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "parson.h"

#define MAX_CONNECTIONS 100
#define MAX_OPERATIONS 10
#define MAX_COMPONENTS 20
#define MAX_NAME_LENGTH 20

// Structure to store connections
typedef struct
{
    char from[MAX_NAME_LENGTH];
    char to[MAX_NAME_LENGTH];
} Connection;

typedef struct
{
    char name[MAX_NAME_LENGTH];
    char operations[MAX_OPERATIONS][MAX_NAME_LENGTH];
    int operation_count;
} FunctionalUnit;

// Structure to store the PE data
typedef struct
{
    char name[MAX_NAME_LENGTH];
    char inputs[MAX_COMPONENTS][MAX_NAME_LENGTH];
    int input_count;
    char outputs[MAX_COMPONENTS][MAX_NAME_LENGTH];
    int output_count;
    char muxes[MAX_COMPONENTS][MAX_NAME_LENGTH];
    int mux_count;
    int mux_bits[MAX_COMPONENTS]; // Bits for each MUX
    char registers[MAX_COMPONENTS][MAX_NAME_LENGTH];
    int register_count;
    FunctionalUnit fus[MAX_COMPONENTS];
    int fu_count;
    int fu_bits[MAX_COMPONENTS];
    Connection connections[MAX_CONNECTIONS];
    int connection_count;
} PE;

#define NUM_STD_OPS 11
const char opcodes[NUM_STD_OPS][MAX_NAME_LENGTH] = {"add", "sub", "mul", "div", "and", "or", "xor", "sll", "sra", "lt", "ge"};
const char ops[NUM_STD_OPS][3] = {"+", "-", "*", "/", "&", "|", "^", "<<", ">>", "<", ">="};

// Function to count MUX inputs
void calculate_mux_bits(PE *pe)
{
    for (int i = 0; i < pe->mux_count; i++)
    {
        int count = 0;
        for (int j = 0; j < pe->connection_count; j++)
        {
            if (strcmp(pe->connections[j].to, pe->muxes[i]) == 0)
            {
                count++;
            }
        }
        pe->mux_bits[i] = (count > 1) ? (32 - __builtin_clz(count - 1)) : 1; // log2 rounding up
    }
}

void calculate_fu_bits(PE *pe)
{
    for (int i = 0; i < pe->fu_count; i++)
    {
        pe->fu_bits[i] = (pe->fus[i].operation_count > 1) ? (32 - __builtin_clz(pe->fus[i].operation_count - 1)) : 1; // log2 rounding up
    }
}

// Function to parse PE from JSON
PE parse_pe_json(const char *filename)
{
    PE pe = {0};

    JSON_Value *root_value = json_parse_file(filename);
    JSON_Object *root_obj = json_value_get_object(root_value);
    JSON_Object *pe_obj = json_object_get_object(root_obj, "PE");

    const char *pe_name = json_object_get_string(pe_obj, "name");
    strncpy(pe.name, pe_name, strlen(pe_name));

    // Parse inputs
    JSON_Array *inputs_array = json_object_get_array(pe_obj, "inputs");
    pe.input_count = json_array_get_count(inputs_array);
    for (int i = 0; i < pe.input_count; i++)
    {
        strcpy(pe.inputs[i], json_array_get_string(inputs_array, i));
    }

    // Parse inputs
    JSON_Array *outputs_array = json_object_get_array(pe_obj, "outputs");
    pe.output_count = json_array_get_count(outputs_array);
    for (int i = 0; i < pe.output_count; i++)
    {
        strcpy(pe.outputs[i], json_array_get_string(outputs_array, i));
    }

    // Parse MUXes
    JSON_Array *muxes_array = json_object_get_array(pe_obj, "muxes");
    pe.mux_count = json_array_get_count(muxes_array);
    for (int i = 0; i < pe.mux_count; i++)
    {
        strcpy(pe.muxes[i], json_array_get_string(muxes_array, i));
    }

    // Parse MUXes
    JSON_Array *regs_array = json_object_get_array(pe_obj, "registers");
    pe.register_count = json_array_get_count(regs_array);
    for (int i = 0; i < pe.register_count; i++)
    {
        strcpy(pe.registers[i], json_array_get_string(regs_array, i));
    }

    // Parse FUs
    JSON_Array *fus_array = json_object_get_array(pe_obj, "fus");
    pe.fu_count = json_array_get_count(fus_array);
    for (int i = 0; i < pe.fu_count; i++)
    {
        JSON_Object *fu_obj = json_array_get_object(fus_array, i);
        strcpy(pe.fus[i].name, json_object_get_string(fu_obj, "name"));
        JSON_Array *fu_ops = json_object_get_array(fu_obj, "ops");
        pe.fus[i].operation_count = json_array_get_count(fu_ops);
        for (int j = 0; j < pe.fus[i].operation_count; j++)
        {
            strcpy(pe.fus[i].operations[j], json_array_get_string(fu_ops, j));
        }
    }

    // Parse connections
    JSON_Array *conn_array = json_object_get_array(pe_obj, "connections");
    pe.connection_count = json_array_get_count(conn_array);
    for (int i = 0; i < pe.connection_count; i++)
    {
        JSON_Object *conn_obj = json_array_get_object(conn_array, i);
        strcpy(pe.connections[i].from, json_object_get_string(conn_obj, "from"));
        strcpy(pe.connections[i].to, json_object_get_string(conn_obj, "to"));
    }

    // Determine MUX bits
    calculate_mux_bits(&pe);
    calculate_fu_bits(&pe);

    json_value_free(root_value);
    return pe;
}

// Function to print parsed PE
void print_pe(const PE *pe)
{
    printf("Parsed PE:\n");
    printf("  Inputs: ");
    for (int i = 0; i < pe->input_count; i++)
    {
        printf("%s ", pe->inputs[i]);
    }
    printf("\n");
    printf("  Outputs: ");
    for (int i = 0; i < pe->output_count; i++)
    {
        printf("%s ", pe->outputs[i]);
    }
    printf("\n");
    printf("  MUXes:\n");
    for (int i = 0; i < pe->mux_count; i++)
    {
        printf("    %s (%d bits)\n", pe->muxes[i], pe->mux_bits[i]);
    }
    printf("  Registers: ");
    for (int i = 0; i < pe->register_count; i++)
    {
        printf("%s ", pe->registers[i]);
    }
    printf("\n");
    printf("  FUs:\n");
    for (int i = 0; i < pe->fu_count; i++)
    {
        printf("    %s: ", pe->fus[i].name);
        for (int j = 0; j < pe->fus[i].operation_count; j++)
            printf("%s ", pe->fus[i].operations[j]);
        printf("(%d)\n", pe->fus[i].operation_count);
    }
    printf("  Connections:\n");
    for (int i = 0; i < pe->connection_count; i++)
    {
        printf("    %s -> %s\n", pe->connections[i].from, pe->connections[i].to);
    }
}

/***************************************************
 * Verilog Generation
 */

char *int_to_binary(int num, int bits, char *binary_str)
{
    // Loop to only print the last 'bits' bits
    for (int i = bits - 1; i >= 0; i--)
    {
        // Store the bit in the binary string
        binary_str[bits - 1 - i] = (num >> i) & 1 ? '1' : '0';
    }
    binary_str[bits] = '\0'; // Null-terminate the string
    return binary_str;
}

int is_input_in_array(const char inputs[MAX_COMPONENTS][MAX_NAME_LENGTH], const char *input)
{
    for (int i = 0; i < MAX_COMPONENTS; i++)
    {
        if (strcmp(inputs[i], input) == 0)
        {
            return 1; // String found
        }
    }
    return 0; // String not found
}

void to_lowercase(char *str)
{
    while (*str)
    {
        *str = tolower((unsigned char)*str); // Convert each character to lowercase
        str++;
    }
}

FILE *VGenHeader(const PE *pe)
{

    int i;
    char vFilename[MAX_NAME_LENGTH + 2] = {0};
    strncpy(vFilename, pe->name, strlen(pe->name));
    vFilename[strlen(pe->name)] = '.';
    vFilename[strlen(pe->name) + 1] = 'v';
    vFilename[strlen(pe->name) + 2] = '\0';

    FILE *vfp = fopen(vFilename, "w+");

    if (vfp == NULL)
    {
        printf("ERROR: Failed to open the input file.\n");
        return NULL;
    }

    // Write module name
    fprintf(vfp, "module %s(\n", pe->name);

    // Instanciate Inputs
    for (i = 0; i < pe->input_count; i++)
    {
        fprintf(vfp, "\tinput %s[31:0]", pe->inputs[i]);
        if (i < pe->input_count - 1 || pe->output_count > 0 || pe->mux_count > 0)
            fprintf(vfp, ",");
        fprintf(vfp, "\n");
    }

    if (pe->register_count > 0)
    {
        fprintf(vfp, "\tinput clk,\n\tinput rstz");
        if (pe->mux_count > 0 || pe->output_count > 0 || pe->fu_count > 0)
            fprintf(vfp, ",");
        fprintf(vfp, "\n");
    }

    // Instanciate Mux selects
    for (i = 0; i < pe->mux_count; i++)
    {
        fprintf(vfp, "\tinput %s_sel", pe->muxes[i]);
        if (pe->mux_bits[i] > 1)
            fprintf(vfp, "[%d:0]", pe->mux_bits[i] - 1);
        if (i < pe->mux_count - 1 || pe->output_count > 0 || pe->fu_count > 0)
            fprintf(vfp, ",");
        fprintf(vfp, "\n");
    }

    // Instanciate FU selects
    for (i = 0; i < pe->fu_count; i++)
    {
        fprintf(vfp, "\tinput %s_sel", pe->fus[i].name);
        if (pe->fu_bits[i] > 1)
            fprintf(vfp, "[%d:0]", pe->fu_bits[i] - 1);
        if (i < pe->fu_count - 1 || pe->output_count > 0)
            fprintf(vfp, ",");
        fprintf(vfp, "\n");
    }

    // Instanciate Outputs
    for (i = 0; i < pe->output_count; i++)
    {
        fprintf(vfp, "\toutput %s[31:0]", pe->outputs[i]);
        if (i < pe->output_count - 1)
            fprintf(vfp, ",");
        fprintf(vfp, "\n");
    }

    fprintf(vfp, ");\n\n");

    printf("Generated module header successfully.\n");

    return vfp;
}

void VGenWires(PE *pe, FILE *vfp)
{
    // Instantiate Mux Outs
    for (int i = 0; i < pe->mux_count; i++)
    {
        fprintf(vfp, "wire[31:0] %s_out;\n", pe->muxes[i]);
    }
    if (pe->mux_count > 0)
        fprintf(vfp, "\n");

    // Instantiate Registers
    for (int i = 0; i < pe->register_count; i++)
    {
        fprintf(vfp, "reg[31:0] %s;\n", pe->registers[i]);
    }
    if (pe->register_count > 0)
        fprintf(vfp, "\n");

    // Instantiate FU outs
    for (int i = 0; i < pe->fu_count; i++)
    {
        fprintf(vfp, "wire[31:0] %s_out;\n", pe->fus[i].name);
    }
    if (pe->fu_count > 0)
        fprintf(vfp, "\n");

    printf("Instantiated Wires.\n");
}

void VGenMux2b(char mux[MAX_NAME_LENGTH], char in0[MAX_NAME_LENGTH], char in1[MAX_NAME_LENGTH], FILE *vfp)
{
    fprintf(vfp, "assign %s_out = %s_sel ? %s : %s;\n", mux, mux, in0, in1);
}

void VGenMuxes(PE *pe, FILE *vfp)
{

    char binary_str[33];
    for (int i = 0; i < pe->mux_count; i++)
    {
        fprintf(vfp, "assign %s_out = ", pe->muxes[i]);
        int count = 0;
        for (int j = 0; j < pe->connection_count; j++)
        {
            if (strcmp(pe->connections[j].to, pe->muxes[i]) == 0)
            {
                if (is_input_in_array(pe->inputs, pe->connections[j].from) || is_input_in_array(pe->registers, pe->connections[j].from))
                    fprintf(vfp, "(%s_sel == %d'b%s) ? %s :\n\t\t\t\t  ", pe->muxes[i], pe->mux_bits[i],
                            int_to_binary(j, pe->mux_bits[i], binary_str), pe->connections[j].from);
                else
                    fprintf(vfp, "(%s_sel == %d'b%s) ? %s_out :\n\t\t\t\t  ", pe->muxes[i], pe->mux_bits[i],
                            int_to_binary(j, pe->mux_bits[i], binary_str), pe->connections[j].from);
            }
        }
        fprintf(vfp, "32'hxxxx;\n\n");
    }

    printf("Generated Multiplexers.\n");
}

void VGenFUs(PE *pe, FILE *vfp)
{

    for (int i = 0; i < pe->fu_count; i++)
    {

        char fu_inputs[MAX_COMPONENTS][MAX_NAME_LENGTH];
        int idx = 0;
        for (int j = 0; j < pe->connection_count; j++)
        {
            if (!strcmp(pe->connections[j].to, pe->fus[i].name))
            {
                strcpy(fu_inputs[idx++], pe->connections[j].from);
            }
        }
        // Skip any FU that was defined with less than 2 inputs
        if (idx < 2)
            continue;

        for (int j = 0; j < pe->fus[i].operation_count; j++)
        {
            to_lowercase(pe->fus[i].operations[j]);
            for (int k = 0; k < NUM_STD_OPS; k++)
            {
                if (!strcmp(pe->fus[i].operations[j], opcodes[k]))
                {
                    // Assume FUs only have 2 inputs and use those two
                    fprintf(vfp, "assign %s_%s = ", pe->fus[i].name, opcodes[k]);
                    if (!is_input_in_array(pe->inputs, fu_inputs[0]) && !is_input_in_array(pe->registers, fu_inputs[0]))
                        fprintf(vfp, "%s_out %s %s", fu_inputs[0], ops[k], fu_inputs[1]);
                    else
                        fprintf(vfp, "%s %s %s", fu_inputs[0], ops[k], fu_inputs[1]);
                    if (!is_input_in_array(pe->inputs, fu_inputs[1]) && !is_input_in_array(pe->registers, fu_inputs[1]))
                        fprintf(vfp, "_out");
                    fprintf(vfp, ";\n");
                }
            }
        }

        fprintf(vfp, "assign %s_out = ", pe->fus[i].name);
        for (int j = 0; j < pe->fus[i].operation_count; j++)
        {
            char binary_str[33];
            for (int k = 0; k < NUM_STD_OPS; k++)
            {
                if (!strcmp(pe->fus[i].operations[j], opcodes[k]))
                {
                    fprintf(vfp, "(%s_sel == %d'b%s) ? %s_%s :\n\t\t\t\t  ", pe->fus[i].name, pe->fu_bits[i],
                            int_to_binary(j, pe->fu_bits[i], binary_str), pe->fus[i].name, opcodes[k]);
                }
            }
        }
        fprintf(vfp, "32'hxxxx;\n\n");
    }
    printf("Generated Functional Units.\n");
}

void VGenRegisters(PE *pe, FILE *vfp)
{
    for (int i = 0; i < pe->register_count; i++)
    {
        for (int j = 0; j < pe->connection_count; j++)
        {
            if (strcmp(pe->connections[j].to, pe->registers[i]) == 0)
            {
                fprintf(vfp, "always @(posedge clk) begin\n\tif (rstz == 0)\n\t\t%s <= 0;\n\telse\n\t\t%s <= %s",
                        pe->registers[i], pe->registers[i], pe->connections[j].from);

                if (!is_input_in_array(pe->inputs, pe->connections[j].from) && !is_input_in_array(pe->registers, pe->connections[j].from))
                    fprintf(vfp, "_out");
                fprintf(vfp, ";\n\tendif\nend\n\n");

                break;
            }
        }
    }

    printf("Generated Registers.\n");
}

void VGenOutputs(PE *pe, FILE *vfp)
{

    char binary_str[33];
    for (int i = 0; i < pe->output_count; i++)
    {
        for (int j = 0; j < pe->connection_count; j++)
        {
            if (strcmp(pe->connections[j].to, pe->outputs[i]) == 0)
            {
                if (!is_input_in_array(pe->inputs, pe->connections[j].from) && !is_input_in_array(pe->registers, pe->connections[j].from))
                    fprintf(vfp, "assign %s = %s_out;\n", pe->outputs[i], pe->connections[j].from);
                else
                    fprintf(vfp, "assign %s = %s;\n", pe->outputs[i], pe->connections[j].from);
                break;
            }
        }
    }
    fprintf(vfp, "\n");

    printf("Generated outputs.\n");
}

void VGenEnd(FILE *vfp)
{
    fprintf(vfp, "endmodule");
    fclose(vfp);
    printf("Module generated successfully.\n");
}

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        fprintf(stderr, "Usage: %s <json_file>\n", argv[0]);
        return 1;
    }

    PE pe = parse_pe_json(argv[1]);
    print_pe(&pe);

    FILE *fp = VGenHeader(&pe);
    VGenWires(&pe, fp);
    VGenMuxes(&pe, fp);
    VGenFUs(&pe, fp);
    VGenRegisters(&pe, fp);
    VGenOutputs(&pe, fp);
    VGenEnd(fp);
    return 0;
}
