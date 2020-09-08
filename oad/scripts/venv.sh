#!/bin/bash
# This script is not meant to be called directly. Use the Makefile included.

sudo virtualenv ./auth && source ./auth/bin/activate && pip install -r project/third_party/requirements.txt
