# Fuzz4PA

A tool for generating protocol abstractions from Solidity smart contracts using the Echidna fuzzer. Fuzz4PA automatically generates visual graphs that represent the behavior of the contracts.

## Overview

Fuzz4PA analyzes smart contracts to generate two types of abstractions:

- **Requires**: also named EPAs (Enabledness-Preserving Abstractions), which focus on the enabledness of contract functions and their preconditions.
- **Enumeration**: also called states abstractions, they usually focus on the state of the contract given by a state variable of type `enum`.

The tool uses Echidna fuzzing to explore contract behavior and automatically generates PDF visualizations of the resulting abstractions.

## Setup

### Installation

- Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

- Install the Echidna fuzzer by following the instructions in the [Echidna repository](https://github.com/crytic/echidna?tab=readme-ov-file#installation).

### Directory Structure

To analyze a contract, place the files in the appropriate directories within the `app/` folder:

- **Solidity contracts**: Place `.sol` files in `app/Contracts/`
- **Configuration files**: Place Python config files in `app/Configs/`

Contracts must be written in **Solidity version 0.8 or higher** for the tool to work correctly.

### Example Structure

```text
app/
├── Contracts/
│   └── MyContract.sol
├── Configs/
│   └── MyContractConfig.py
└── fuzz4pa.py
```

## Usage

From the `app/` directory, run the main script:

```bash
python fuzz4pa.py <config_name> mode=<e|s> [testlimit=<number>]
```

### Parameters

- `<config_name>`: Name of the configuration file (without `.py` extension)
- `mode=requires|enum`: Analysis mode(`requires` for Requires, `enum` for Enumeration) - **required**
- `testlimit=<number>`: Number of function calls done by Echidna in its fuzzing campaign (default: 50,000)

### Examples

```bash
# Generate Requires with 100,000 function calls
python fuzz4pa.py RoomThermostatConfig mode=requires testlimit=100000

# Use default test limit (50,000)
python fuzz4pa.py MyContractConfig mode=requires
```

## Output

The tool generates:

- **PDF visualization**: Saved to `results/<contract>/<mode>/<testlimit>/`
- **A .dot file** in the same directory, which can be used for further analysis or visualization with tools like Graphviz.

The final PDF path will be displayed upon completion.
