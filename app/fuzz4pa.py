""" Fuzz4PA - Entry point for running the abstractor with Echidna """

import sys
from time import time
import os
from threading import Thread
from rich.console import Console
import graphviz


from modules.contract_creation import ContractCreator
from modules.tools_configs import EchidnaConfigData
from modules.tools_runners import EchidnaRunner
from modules.contract_config import ConfigVariables, ConfigImporter, Mode
from modules.output import Graph, OutputPrinter
from modules.file_manager import create_directory
from modules.compact_states import format_graph_file


sys.path.append("../")
sys.path.append("Configs")
sys.path.append("modules/")

console = Console()

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
    config_variables.dir_name = f"../results/{config_variables.contractFileName[:-4]}/{mode.name}/{budget}"
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
    
    # Echidna-specific parameters
    test_limit = None
    budget = None

    debug = False
    output = False

    verbose = False 
    time_mode = False 

    optimization_settings = Optimizer()
    # No flags applied by default - all optimizations enabled

    # Parse command line arguments - using key-value pairs
    # Usage: python fuzz4pa.py <contract_config> [key=value] [--flags]
    if len(sys.argv) < 2:
        print("Usage: python fuzz4pa.py <contract_config> [key=value] [--flags]")
        print("  contract_config: name of the contract configuration")
        print("  key=value options:")
        print("    mode=enum|requires        : 'enum' for enumeration or 'requires' for requires (required)")
        print("    testlimit=<num> : test limit for echidna (default: 50000)")
        print("  flags:")
        print("    --debug         : enable debug mode")
        print("    --print-output  : enable output printing")
        sys.exit(1)

    contract_config = sys.argv[1]
    
    # Initialize mode as None to check if it was provided
    mode = None
    
    # Parse key-value pairs and flags starting from index 2
    for i in range(2, len(sys.argv)):
        arg = sys.argv[i]
        
        if "=" in arg:
            key, value = arg.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == "mode":
                if value.lower() == "e" or value.lower() == "epa" or value.lower() == "requires":
                    mode = Mode.requires
                elif value.lower() == "s" or value.lower() == "states" or value.lower() == "enum":
                    mode = Mode.enumeration
                else:
                    raise InvalidParametersException("Invalid mode, must be 'e' or 's'.")
            elif key == "testlimit":
                try:
                    test_limit = int(value)
                    budget = test_limit
                except ValueError:
                    raise InvalidParametersException(f"Invalid testlimit value: {value}. Must be an integer.")
            else:
                print(f"Warning: Unknown parameter '{key}' - ignoring")
        elif arg == "--debug":
            print("\nRunning Fuzz4PA in debug mode with the following parameters:")
            debug = True
        elif arg == "--print-output":
            output = True
        else:
            print(f"Warning: Ignoring parameter '{arg}' - use key=value format or --flags")
    
    # Check if mode was provided
    if mode is None:
        raise InvalidParametersException("Mode is required. Use mode=requires for Requires or mode=enum for Enumeration abstractions.")

    # Import the config module
    config = __import__(contract_config, level=0)
    
    # Set default test_limit for echidna if not provided
    if test_limit is None:
        test_limit = 50_000
        budget = test_limit

    main()

    end = time()
    console.print(f"\n[bold]Total time: {end - start:.2f}s", highlight=False)
