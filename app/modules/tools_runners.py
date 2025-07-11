from time import time
import subprocess
import re
from dataclasses import asdict
import subprocess
from rich.console import Console

from modules.contract_config import Mode
from modules.output import output_combination

console = Console()

verbose = False 

class EchidnaRunner:
    def __init__(self, config_variables, contract, config_file_params):
        self.directory = config_variables.dir
        self.contract_name = config_variables.contractName
        self.contract = contract
        self.config_file_params = config_file_params
        self.config_variables = config_variables

    def run_contract(self):
        start = time()
        result = self.set_up_and_run()
        end = time()
        if self.config_variables.debug:
            print(f"This contract took {round(end - start, 2)}s")
        return self.process_output(result)

    def set_up_and_run(self):
        tool_command = self.create_echidna_command()
        result = self.run_echidna_command(tool_command)
        return result

    def create_echidna_command(self):
        config_file = self.create_config_file()
        commandResult = (
            f"echidna {self.contract} --contract {self.contract_name} --config {config_file}"
        )
        return commandResult

    def run_echidna_command(self, command_to_run):
        result = subprocess.run([command_to_run, ""], shell=True, cwd=self.directory, capture_output=True)
        if result.stderr:
            console.print(f"[bold bright_red]Error in Echidna execution!")
            raise Exception(result.stderr.decode("utf-8"))
        return result.stdout.decode("utf-8")

    def process_output(self, tool_result):
        tests_that_failed = []
        for line in tool_result.splitlines():
            if "failed!" in line:
                match = re.search(r"vc(\w+)\(", line)
                if match:
                    failed_test = match.group(1)  # vcIxJxK(¡): -> IxJxK.
                else:
                    continue  # Por si falla un assert que no tiene que ver con los tests
                i, j, k = get_params_from_function_name(failed_test)
                tests_that_failed.append(([i, j, k], ""))
        return tests_that_failed

    def create_config_file(self):
        new_file_name = f"{self.directory}/config.yaml"
        newfile = open(new_file_name, "w")
        for key, value in asdict(self.config_file_params).items():
            newfile.write(f"{key}: {value} \n")
        newfile.close()
        return new_file_name

# Pure
def get_params_from_function_name(temp_function_name):
    array = temp_function_name.split("x")
    return int(array[0]), int(array[1]), int(array[2])
