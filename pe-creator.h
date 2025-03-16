#ifndef PE_CREATOR_H
#define PE_CREATOR_H

#define MAX_CONNECTIONS 100
#define MAX_COMPONENTS 20
#define MAX_NAME_LENGTH 20

// Structure to store connections
typedef struct
{
    char from[MAX_NAME_LENGTH];
    char to[MAX_NAME_LENGTH];
} Connection;

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
    char fus[MAX_COMPONENTS][MAX_NAME_LENGTH];
    int fu_count;
    Connection connections[MAX_CONNECTIONS];
    int connection_count;
} PE;

#endif