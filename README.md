# HARP-CH4
L2 Data from SCIAMACHY and TROPOMI to L3 using HARP

For SCIAMACHY's Data, it was necessary to use the CODA package in Python, so the whole code is in Python.
It uses CODA to import specific parameters necessary for the quality filters of the CH4 data, that were not available with HARP only.
The package rasterio is used to generate the L3 Data.

