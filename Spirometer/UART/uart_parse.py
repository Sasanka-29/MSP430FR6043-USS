#!/usr/bin/python
""" Parses USS Template project UART data (src.csv) and store result in out.csv"""
import re
import struct
import sys

def decode_file(file_in_name, file_out_name):
    """ Decodes input file using delim_dict and stores decoded output"""
    delim_dict = {"$": "AbsTof-UPS", "#": "AbsTof-DNS", "%": "DToF", "!": "VFR"}
    # Open File Input and Output Files
    input_file = open(file_in_name, "r")
    target_file = open(file_out_name, "w")
    # Iterate through the data
    for line in input_file:
        # Remove New Line
        line = line.rstrip("\n")
        # Remove Spaces in front
        line = line.lstrip(" ")
        # Remove White space and tabs
        pattern = re.compile(r"\s+")
        clean_line = re.sub(pattern, " ", line)
        # Split the line by spaces
        line_list = clean_line.split(",")
        # Check if the first Value is supported by dictionary
        if line_list[0] in delim_dict.keys():
            target_file.write(delim_dict[line_list[0]])
        else:
            target_file.write("Undefined " + line_list[0])
        target_file.write(",")
        result = struct.unpack("f", struct.pack("I", int(line_list[1], 16)))[0]
        # Format the output in exponent notation
        target_file.write("{0:e}".format(result) + "\n")
    # Close Files
    input_file.close()
    target_file.close()
    print("Successfully Generated: \n", file_out_name)
    return

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Invalid input. Usage uart_parser.py <input_csv> <output_csv>")
    else:
        # Parse the USS Template project src input file and store result in
        # output csv
        decode_file(sys.argv[1], sys.argv[2])



