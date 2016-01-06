# plaster
clustering algorithms designed for identifying significant places in gps data

# Intro
Normal clustering algos are often too general for extracting places from GPS data; i.e. we should not identify an intersection of frequent paths as a significant location simply because of the density of measurements. Plaster includes the algorithm described in 'Extracting Places from Traces of Locations' by Kang et. al. (2004) as well as modifications thereof.

#Dependencies
The only dependency is numpy and scipy
