## Purpose

This tool is designed to run on an Arduino connected to a Gallagher controller as a reader. It will repeatedly send a range of valid/invalid card data to the controller and accurately record all its responses, outputting JSON-based logs. These logs can then in turn be processed by the [sampler-grapher](../sampler-grapher/) tool in an attempt to find possible timing attack vulnerabilities.


## Requirements

An installation of [Arduino-Makefile](https://github.com/sudar/Arduino-Makefile) and the [TimerOne](https://github.com/PaulStoffregen/TimerOne) library are required.


## Building

Check the makefile for instructions.
