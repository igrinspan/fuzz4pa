""" Fuzz4PA - Entry point for running the abstractor with Echidna """

import sys
from time import time
import os
from threading import Thread
from rich.console import Console
import graphviz
import argparse


from modules.contract_creation import ContractCreator
from modules.tools_configs import EchidnaConfigData
from modules.tools_runners import EchidnaRunner
from modules.contract_config import ConfigVariables, ConfigImporter, Mode
from modules.output import Graph, OutputPrinter
from modules.file_manager import create_directory
from modules.compact_states import format_graph_file
from modules.generate_config import create_config_file


sys.path.append("../")
sys.path.append("Configs")
sys.path.append("Contracts")
sys.path.append("modules/")

console = Console()

def get_contract_path(contract_name):
    # Directory where fuzz4pa.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Build full path
    contract_path = os.path.join(
        base_dir,
        "Contracts",
        f"{contract_name}.sol"
    )

    return contract_path

import os
import shutil

def clean_results(contract, mode, testlimit):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    base_path = os.path.join(
        project_root, "fuzz4pa_results", contract, mode.value, str(testlimit)
    )
    graph_path = os.path.join(base_path, "graph")

    # Remove everything except graph folder
    for item in os.listdir(base_path):
        full_path = os.path.join(base_path, item)
        if item != "graph":
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

    # Inside graph, keep only .pdf and .dot
    for file in os.listdir(graph_path):
        if not file.endswith(".pdf") and not file.endswith(".enumeration") and not file.endswith(".requires"):
            os.remove(os.path.join(graph_path, file))

class InvalidParametersException(Exception):
    pass

def create_config_variables():
    # Creamos el objeto en el que vamos a guardar las variables.
    config_variables = ConfigVariables()

    # Creamos el objeto que va a importar y hacer el setUp de esas variables. 
    config = __import__(contract_config, level=0)
    importer = ConfigImporter(config, config_variables, optimization_settings)
    
    config_variables = importer.config_variables_setup(mode)
    config_variables.debug = debug
    return config_variables

def echidna_execution_logic(config_variables, init_contract_to_run, transitions_contracts_to_run, test_limit):
    """ Runs the contracts with Echidna. Prepares the configFile and calls EchidnaRunner """
    init_failed = []
    tr_failed = []
    init_config_params = EchidnaConfigData(testLimit=test_limit, workers=16, format="text", seqLen=2)
    transitions_config_params = EchidnaConfigData(testLimit=test_limit, workers=16, format="text")


    print("  Running the init contract...")
    valid_init_time = time()
    init_failed = EchidnaRunner(config_variables, init_contract_to_run, init_config_params).run_contract()
    time_str = f"{time() - valid_init_time:.2f}s"
    console.print(f"  [green]✓[/green] Init contract time: {time_str}", highlight=False)

    if debug:
        console.print("  Running the transitions contract(s)...")
    transitions_time = time()
    for id, contract in enumerate(transitions_contracts_to_run):
        # contract_file = f"{contract.split("/")[-5]}/{contract.split("/")[-4]}/{contract.split("/")[-3]}/{contract.split("/")[-1]}"  # Get the file name from the path
        print(f"  Running the transitions contract number {id}...")
        try:
            tr_failed += EchidnaRunner(config_variables, contract, transitions_config_params).run_contract()
            print(f"  Elapsed time until now: {time() - transitions_time:.2f}s")
        except Exception as e:
            console.print(f"  [red]Error running the transitions contract: {contract}[/red]")
            console.print(f"  [red]{e}[/red]")
    console.print(f"  [green]✓[/green] Transitions contracts time: {time() - transitions_time:.2f}s", highlight=False)

    return init_failed, tr_failed

def main():
    
    # Importamos y guardamos las variables (preconditions, states, functions, etc.)
    config_variables = create_config_variables()

    # if debug:
    console.print(f"\n[bold deep_sky_blue1]Contract[/bold deep_sky_blue1]: {config_variables.contractName}")
    console.print(f"[bold deep_sky_blue1]Abstraction Type[/bold deep_sky_blue1]: {mode.name}")
    console.print(f"[bold deep_sky_blue1]Echidna's Test Limit[/bold deep_sky_blue1]: {test_limit}\n")

    # Define where the results will be saved, both the contracts to run and the graph.
    config_variables.dir_name = f"../fuzz4pa_results/{config_variables.contractFileName[:-4]}/{mode.name}/{budget}"
    config_variables.dir = create_directory(config_variables.dir_name) # devuelve el path completo.

    console.print("[bold bright_green underline]Creating contracts to run...")
    contract_creation_time = time()
    # Creamos los contratos.
    contract_creator = ContractCreator().create_contract_creator(config_variables, tool)

    init_contract_to_run, init_queries_names = contract_creator.create_init_contract()
    transitions_contracts_to_run, queries_per_contract = contract_creator.create_multiple_transitions_contracts()
    console.print(f"  [green]✓[/green] Contract creation time: {time() - contract_creation_time:.2f}s \n", highlight=False)

    execution_time = time()
    init_failed = []
    tr_failed = []
    try:
        console.print("[bold bright_green underline]Executing init and transition contracts...")
        init_failed, tr_failed = echidna_execution_logic(config_variables, init_contract_to_run, transitions_contracts_to_run, test_limit)
    except Exception as e:
        console.print(f"[bold bright_red]Could not run contract {config_variables.contractName} with Echidna in mode {mode.name}.\nError: {e}")
        return
    console.print(f"  [green]✓[/green] Execution time: {time() - execution_time:.2f}s \n", highlight=False)

    # if output or debug:
    # OutputPrinter(config_variables).print_results(tr_failed, init_failed)

    graph_time = time()
    console.print("[bold bright_green underline]Building graph...")
    result_graph = Graph(config_variables).build_graph(init_failed, tr_failed)

    # Reformatear el archivo del grafo generado
    try:
        graph_file_path = os.path.abspath(f"{config_variables.dir}/graph/{config_variables.contractName}_Mode.{mode.name}")
        new_graph_content = format_graph_file(graph_file_path)
        src = graphviz.Source(new_graph_content)
        src.render(graph_file_path, format='pdf')

    except Exception as e:
        console.print(f"  [yellow]Warning: Could not format graph file: {e}[/yellow]")

    console.print(f"  [green]✓[/green] Graph construction time: {time() - graph_time:.2f}s \n", highlight=False)

    # if debug:
    console.print("[bold bright_green underline]Final results:")
    console.print(f"  Number of abstract states: [bright_green]{len(result_graph.nodes)}")
    console.print(f"  Number of transitions exiting from the constructor: [bright_green]{len(init_failed)}")
    console.print(f"  Number of internal transitions: [bright_green]{len(tr_failed)}")

    clean_results(sol_file, mode, test_limit)
    
    # Show the user where to find the resulting graph/abstraction
    pdf_path = os.path.abspath(f"{config_variables.dir}/graph/{config_variables.contractName}_Mode.{mode.name}.pdf")
    console.print(f"\n[bold]Abstraction saved to:[/bold]")
    console.print(pdf_path)

class Optimizer():
    """ Class to save optimization flags. """
    def __init__(self):
        self.reduce_true = True
        self.reduce_equal = True
        self.flag_mapping = {
            "-rt": {"reduce_true": False}, # rt = reduce true (disables this optimization)
            "-re": {"reduce_equal": False}, # re = reduce equal (disables this optimization)
            "-rte": {"reduce_equal": False, "reduce_true": False}, # rte = reduce true and equal
        }

    def __str__(self): 
        return f"reduce_true: {self.reduce_true}\nreduce_equal: {self.reduce_equal}"

    def set_flags(self, flag):
        """ Sets optimization variables according to the flag passed to it """
        if flag in self.flag_mapping:
            flags_to_update = self.flag_mapping[flag]
            for variable, value in flags_to_update.items():
                setattr(self, variable, value)
        else:
            raise InvalidParametersException(f"Unrecognized parameter: {flag}.")


if __name__ == "__main__":

    start = time()

    tool = "echidna"

    sol_file = None
    test_limit = None
    budget = None

    debug = False
    output = False

    verbose = False
    time_mode = False

    optimization_settings = Optimizer()

    parser = argparse.ArgumentParser(
        description="Fuzz4PA - Predicate Abstraction via Fuzzing"
    )

    mode_group = parser.add_mutually_exclusive_group(required=False)

    mode_group.add_argument(
        "--auto",
        metavar="SOL_FILE",
        help="Automatic mode: provide Solidity file"
    )

    mode_group.add_argument(
        "--config",
        help="Advanced mode: provide config module"
    )

    parser.add_argument(
        "--mode",
        choices=["requires", "enum"],
        help="Abstraction mode"
    )

    parser.add_argument(
        "--testlimit",
        type=int,
        help="Echidna test limit (default: 50000)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    parser.add_argument(
        "--print-output",
        action="store_true",
        help="Enable output printing"
    )

    args = parser.parse_args()

    # -------------------------------------------------
    # ZERO ARGUMENT DEMO MODE
    # -------------------------------------------------

    if len(sys.argv) == 1:
        print("[INFO] Running Fuzz4PA demo mode")

        args.config = "HelloBlockchainFixedConfig"
        args.mode = "requires"
        args.testlimit = 10000

    if args.mode is None:
        parser.error("--mode is required (requires or enum)")

    mode = Mode.requires if args.mode == "requires" else Mode.enumeration

    test_limit = args.testlimit if args.testlimit is not None else 50_000
    budget = test_limit

    debug = args.debug
    output = args.print_output

    # -------------------------------------------------
    # AUTOMATIC MODE
    # -------------------------------------------------

    if args.auto is not None:
        sol_file = args.auto
        sol_path = get_contract_path(sol_file)

        if not os.path.exists(sol_path):
            raise InvalidParametersException(
                f"Solidity file not found: {sol_path}"
            )

        print(f"[INFO] Solidity file: {sol_path}")

        generated_config_path = os.path.abspath(
            create_config_file(contract_file_path=sol_path)
        )

        contract_config = generated_config_path.split('/')[-1][:-3]
        print(f"[INFO] generated_config_path: {generated_config_path}")

    elif args.config is not None:
        contract_config = args.config
    else:
        parser.error("You must provide --auto or --config")

    if contract_config in sys.modules:
        del sys.modules[contract_config]

    config = __import__(contract_config, level=0)
    sol_file = config.fileName[:-4]

    if not config.statesNamesModeState and mode == Mode.enumeration:
        raise InvalidParametersException(
            "This contract does not support enumeration mode."
        )

    main()

    end = time()
    console.print(f"\n[bold]Total time: {end - start:.2f}s", highlight=False)


