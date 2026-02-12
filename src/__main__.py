#!/usr/bin/env python3
"""
Allows running the package as: python -m src
"""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
