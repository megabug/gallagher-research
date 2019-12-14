## Purpose

This tool is designed to read the output of the [sampler](../sampler/) tool and produce visual output. This output can be observed to find possible side-channel information leaks in an attempt to find possible timing attack vulnerabilities.


## Requirements

The [Matplotlib](https://matplotlib.org/) library is required.


## Usage

```bash
sampler-grapher.py [valid-facility-code] [output-directory] < sampler-output.json
```

`valid-facility-code` is the numeric facility code that is known to be accepted by the controller. Card data messages sent by the sampler that used this facility code will be highlighted in the output.

`output-directory` is the path to place the output images.
