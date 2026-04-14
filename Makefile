# Root Makefile

# Include all .mk files from the makes directory
include makes/*.mk

# Set the default target (runs when you just type `make`)
.DEFAULT_GOAL := help