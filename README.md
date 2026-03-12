# fuzz4pa

A tool for generating protocol abstractions from Solidity smart contracts using the Echidna fuzzer. Fuzz4PA automatically generates visual graphs that represent the behavior of the contracts.

## Overview

Fuzz4PA analyzes smart contracts to generate two types of abstractions:

- **Requires**: also named EPAs (Enabledness-Preserving Abstractions), which focus on the enabledness of contract functions and their preconditions.
- **Enumeration**: also called states abstractions, they usually focus on the state of the contract given by a state variable of type `enum`.

The tool uses Echidna fuzzing to explore contract behavior and automatically generates PDF visualizations of the resulting abstractions.

## Setup and Usage

To replicate our results, the tool can be easily downloaded and set up using Docker, which ensures a consistent environment for running the analysis. Follow the instructions below to get started. Note that depending on the resources assigned to the container, the analysis may take longer than the time reported in our paper.

1. Pull the image from Docker Hub:

    ```bash
    docker pull igrinspan/fuzz4pa:icst2026
    ```

2. Run the container:

    - Option 1: Simple Demo (with default settings)

        ```bash
        docker run --rm \
        -v $(pwd)/fuzz4pa_results:/fuzz4pa_results \
        igrinspan/fuzz4pa:icst2026
        ```

        This command will execute the tool with a default contract and configuration, providing a quick and easy demonstration of its capabilities.

        You can find the generated PDF and .dot files in the `fuzz4pa_results` directory on your host machine. Depending on your OS, you can access the PDF directly with:

        macOS:

        ```bash
        open fuzz4pa_results/HelloBlockchainFixed/requires/10000/graph/HelloBlockchain_Mode.requires.pdf
        ```

        Linux:

        ```bash
        xdg-open fuzz4pa_results/HelloBlockchainFixed/requires/10000/graph/HelloBlockchain_Mode.requires.pdf
        ```

        Windows:

        ```bash
        start fuzz4pa_results/HelloBlockchainFixed/requires/10000/graph/HelloBlockchain_Mode.requires.pdf
        ```

         Adjust the path as needed based on your operating system.

    - Option 2: Custom Configuration

        Only using the source code of the contract as input (you can replace `BasicProvenanceFixed` with any contract file name in the `app/Contracts/` directory):

        ```bash
        docker run --rm \
        -v $(pwd)/fuzz4pa_results:/fuzz4pa_results \
        igrinspan/fuzz4pa:icst2026 \
        --auto BasicProvenanceFixed \
        --mode requires \
        --testlimit 50000
        ```

        Providing also a configuration file (you can replace `EscrowVaultConfig` with your any available config name in the `app/Configs/` directory):

        ```bash
        docker run --rm \
        -v $(pwd)/fuzz4pa_results:/fuzz4pa_results \
        igrinspan/fuzz4pa:icst2026 \
        --config EscrowVaultConfig \
        --mode enum \
        --testlimit 100000
        ```

        You can change the --mode and adjust the test limit as needed to see how it affects the generated abstractions.

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

### Output

The tool generates:

- **PDF visualization**: Saved to `fuzz4pa_results/<contract>/<mode>/<testlimit>/`
- **A .dot file** in the same directory, which can be used for further analysis or visualization with tools like Graphviz.

The final PDF path will be displayed upon completion.
