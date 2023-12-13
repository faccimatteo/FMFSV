# PEPA Model Parser and Analysis Tool

This Python project provides a tool for parsing Performance Evaluation Process Algebra (PEPA) models and generating the derivation graph and the Continuous Time Markov Chain (CTMC) graph based on user-specified input files.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Input Files](#input-files)
- [Output](#output)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Overview

The tool takes a PEPA model file (`model.pepa`) as input and requires additional files specifying the system states for deriving the graphs. It supports the calculation of both the derivation graph and the CTMC graph.

## Installation

To use the PEPA model parser and analysis tool, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/faccimatteo/FMFSV
   ```

## Usage

Run the main script (main.py) with the following command:

  ```bash
  Copy code
  python main.py --model <path-to-model.pepa>
  Options
  -h, --help: Show the help message and exit.
  --model, -m: Specify the path to the PEPA model file.
  ```
## Input Files

The tool requires additional input files to calculate the derivation graph and the CTMC graph. Ensure the following files are present:

states.py: File containing all system states required for deriving the graphs (both derivation graph and CTMC).

## Output

The tool generates the following output files:

derivation_graph.svg: Image file containing the derivation graph.
ctmc_graph.svg: Image file containing the Continuous Time Markov Chain (CTMC) graph.
Examples

## Examples 

```bash
python main.py --model models/example_model.pepa
```

## Contributing

Contributions are welcome! If you have any improvements or bug fixes, feel free to submit a pull request. For major changes, please open an issue first to discuss the proposed changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
