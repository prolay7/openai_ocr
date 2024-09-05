#!/usr/bin/env python3

# Import the functions from modules
from dbread import connect_and_read
from ocread import connect_and_read_oc
from ocrai import connect_and_read_ocai

 # Call the first function and wait for it to complete
print("Starting connect_and_read...")
connect_and_read()
print("connect_and_read completed.")

# Call the second function and wait for it to complete
# print("Starting connect_and_read_oc...")
# connect_and_read_oc()
# print("connect_and_read_oc completed.")

# Call the third function and wait for it to complete
# print("Starting connect_and_read_ocai...")
# connect_and_read_ocai()
# print("connect_and_read_ocai completed.")