import numpy as np
import os
import math

from modules.file_manager import create_file, write_file, write_file_from_string
from modules.contract_config import Mode
from rich.console import Console

console = Console()

# The ContractCreator receives a config_variables object, from which they extract everything necessary:
# states, preconditions, extraconditions, function_names, function_variables...
# Some utility functions remain at the end of the module that are used by ContractCreator functions.


class ContractCreator:
    # Public methods
    def create_contract_creator(self, config_variables, tool):
        if tool == "echidna":
            return EchidnaContractCreator(config_variables)
        else:
            raise Exception("Invalid tool name")

    def create_init_contract(self):
        # Method is implemented by subclass.
        pass

    def create_multiple_transitions_contracts(self):
        # Method is implemented by subclass.
        pass

    # Private methods
    def transform_contract_for_init(self, filename_temp):
        new_contract_body = self.remove_everything_after_constructor(filename_temp)
        write_file_from_string(filename_temp, new_contract_body)

    def remove_everything_after_constructor(self, filename_temp):
        file_lines = open(filename_temp, "r").readlines()
        _, _, contract_end = self.contract_body(file_lines)
        _, constructor_end = self.get_constructor_start_and_end_lines(file_lines)
        new_contract_lines = file_lines[: constructor_end + 1] + ["}"]
        if contract_end < len(file_lines) - 1:
            new_contract_lines += file_lines[contract_end + 1 :]
        return new_contract_lines

    def contract_body(self, file_lines):
        start = find_contract_start_line(file_lines, self.target_contract)
        end = find_contract_end_line(file_lines, self.target_contract)
        return file_lines[start : end + 1], start, end

    def clean_true_requires(self, body):
        lines = body.replace("require(true);", "").split("\n")
        cleaned_lines = [line for line in lines if line.strip()]
        new_body = "\n".join(cleaned_lines)
        return new_body

    def get_constructor_start_and_end_lines(self, input_file):
        target_constructor_start_line = -1
        target_constructor_end_line = -1

        in_target_contract = False
        in_constructor = False

        for index, line in enumerate(input_file):
            if (line.strip().startswith("contract " + self.target_contract) or 
                line.strip().startswith("abstract contract " + self.target_contract)) and not is_a_comment(line):
                in_target_contract = True
            if in_target_contract and line.strip().startswith("constructor") and not is_a_comment(line):
                in_constructor = True
                target_constructor_start_line = index
            if in_target_contract and in_constructor and line.strip() == "}":
                target_constructor_end_line = index + 1
                break
        return target_constructor_start_line, target_constructor_end_line

    def get_valid_transitions_output(self, preconditions_thread, preconditions, states_thread, extra_conditions_thread, extra_conditions, functions, config_variables):
        # temp_output = ""
        all_queries_names = []
        all_queries = []
        for index_precondition_require, precondition_require in enumerate(preconditions_thread):
            if isinstance(preconditions, np.ndarray):
                preconditions = preconditions.tolist()
            real_index_precondition_require = preconditions.index(precondition_require)
            for index_precondition_assert, precondition_assert in enumerate(preconditions):
                for index_function, function in enumerate(functions):
                    extra_condition_pre = extra_conditions_thread[index_precondition_require]
                    extra_condition_post = extra_conditions[index_precondition_assert]
                    if ((index_function + 1) in states_thread[index_precondition_require] and config_variables.mode == Mode.requires) or config_variables.mode == Mode.enumeration:
                        # Abstract this below into a separate function
                        function_name = get_temp_function_name(real_index_precondition_require, index_precondition_assert, index_function) # Uso el real_index_precondition_require para el nombre de la query.
                        temp_function = functionOutput(function_name, config_variables.functionVariables) + "\n"
                        temp_function += output_transitions_function(
                            precondition_require,
                            function,
                            precondition_assert,
                            index_function,
                            extra_condition_pre,
                            extra_condition_post,
                            config_variables,
                        )
                        temp_function += "\n\t}\n"
                        # temp_output += temp_function
                        all_queries_names.append(function_name)
                        all_queries.append(temp_function)
        
        return all_queries, all_queries_names

    def get_init_output(self, config_variables):
        temp_output = ""
        temp_function_names = []
        for id_precondition_assert, precondition_assert in enumerate(config_variables.preconditions):
            function_name = get_temp_function_name(id_precondition_assert, "0", "0")
            temp_function_names.append(function_name)
            temp_function = functionOutputInit(function_name, config_variables.functionVariables) + "\n"
            temp_function += output_init_function(
                precondition_assert, config_variables.extraConditions[id_precondition_assert]
            )
            temp_output += temp_function + "\n\t}\n"
        return temp_output, temp_function_names

class EchidnaContractCreator(ContractCreator):
    def __init__(self, config_variables):
        self.directory = config_variables.dir
        self.config_variables = config_variables
        self.target_contract = config_variables.contractName

    def create_init_contract(self):
        filename_temp = create_file("init", self.directory, self.config_variables.fileName, self.target_contract)
        body, all_queries_names = self.get_init_output(self.config_variables)
        body = self.clean_true_requires(body)
        write_file(filename_temp, body, self.target_contract)
        self.transform_contract_for_init(filename_temp)
        self.change_for_constructor_fuzzing(filename_temp)
        return filename_temp, all_queries_names

    def create_multiple_transitions_contracts(self):
        pre = self.config_variables.preconditions
        extra = self.config_variables.extraConditions
        queries, function_names = self.get_valid_transitions_output(pre, pre, self.config_variables.states, extra, extra, self.config_variables.functions, self.config_variables)

        queries_count = len(function_names)
        contracts = []
        print(f"  Contract's query count: {queries_count}")
        splits = calculate_optimal_splits(queries_count)
        console.print(f"  [bright_yellow]Queries will be divided into {splits} contracts, each one with approx. {queries_count // splits} queries.")
        queries_splitted = np.array_split(queries, splits)  # Creates an array of query arrays.
        for idx, queries_list in enumerate(queries_splitted):
            body = ""  # Here we put the queries we want for the new contract.
            for query in queries_list:
                body += query
            body = self.clean_true_requires(body)
            filename_temp = create_file(f"transitions_{idx}", self.directory, self.config_variables.fileName, self.target_contract)  # esto hace un archivo nuevo copiando los contenidos de EPXCrowdsale.sol
            write_file(filename_temp, body, self.target_contract)
            contracts.append(filename_temp)

        for contract in contracts:
            self.change_for_constructor_fuzzing(contract)

        return contracts, queries_count // splits

    def change_for_constructor_fuzzing(self, contract_filename):
        has_initialized_initial_code = self.has_initialized_code()
        write_file(contract_filename, has_initialized_initial_code, self.target_contract)

        new_lines = self.add_modifier_to_contract_functions(contract_filename, "hasInitialized")
        change_status = "\thas_initialized = true;\n"
        start, end = self.get_constructor_start_and_end_lines(new_lines)

        constructor_lines = new_lines[start:end]
        for index, line in enumerate(constructor_lines):
            if ")" in line:
                if "public" in line:
                    constructor_lines[index] = line.replace(")", ") hasNotInitialized ", 1)
                else:
                    constructor_lines[index] = line.replace(")", ") hasNotInitialized public", 1)
                break

        constructor_lines[0] = constructor_lines[0].replace("constructor", "function my_constructor")
        constructor_lines[-1] = constructor_lines[-1].replace("}", f"{change_status} {constructor_lines[-1]}")

        new_lines = new_lines[:start] + constructor_lines + new_lines[end:]
        write_file_from_string(contract_filename, new_lines)

    def add_modifier_to_contract_functions(self, contract_filename, modifier_name):
        lines = open(contract_filename, "r", encoding='utf-8').readlines()
        new_lines = []
        in_contract = False
        in_function_declaration = False

        for line in lines:
            if is_contract_declaration(line, self.target_contract):
                in_contract = True
            elif in_contract and is_function_declaration(line):
                in_function_declaration = True

            if in_function_declaration and ")" in line:
                line = line.replace(")", f") {modifier_name}", 1)
                in_function_declaration = False

            line = line.replace("pure", "view") # porque el modifier accede a una variable de estado, deja de ser pure.
            new_lines.append(line)

        return new_lines

    def has_initialized_code(self):
        has_initialized_modifier = self.create_modifier("hasInitialized", ["has_initialized"])
        has_not_initialized_modifier = self.create_modifier("hasNotInitialized", ["!has_initialized"])
        has_initialized_declaration = "\tbool has_initialized = false;\n\n"
        return has_initialized_modifier + has_not_initialized_modifier + has_initialized_declaration

    def create_modifier(self, name, require_clauses):
        res = f"\tmodifier {name} {{\n"
        for require in require_clauses:
            res += f"\t\trequire({require});\n"
        res += "\t\t_;\n"
        res += "\t}\n\n"
        return res

def find_contract_start_line(contract_lines, contract_name):
    for idx, line in enumerate(contract_lines):
        if f"contract {contract_name}" in line and not is_a_comment(line):
            return idx

def find_contract_end_line(contract_lines, contract_name):
    inside_function = False
    bracket_count = 0
    start_position = find_contract_start_line(contract_lines, contract_name)

    for idx, line in enumerate(contract_lines):
        if idx == start_position:
            bracket_count = 1
            inside_function = True
            continue

        if inside_function and "{" in line and not is_a_comment(line):
            bracket_count += 1
        if inside_function and "}" in line and not is_a_comment(line):
            bracket_count -= 1
        if inside_function and bracket_count == 0:
            return idx

    return -1

def is_contract_declaration(line, contract_name):
    return (line.strip().startswith("contract " + contract_name) or 
        line.strip().startswith("abstract contract " + contract_name)) and not is_a_comment(line)

def is_function_declaration(line):
    return line.strip().startswith("function") and not is_a_comment(line)

def is_constructor_declaration(line):
    return line.strip().startswith("constructor") and not is_a_comment(line)

def is_a_comment(line):
    return any(line.strip().startswith(prefix) for prefix in ["//", "/*", "*", "*/"])

def functionOutput(number, function_variables):
    return "\tfunction vc" + number + "(" + function_variables + ") payable public {"

def functionOutputInit(number, function_variables):
    return "\tfunction vc" + number + "(" + function_variables + ") public {"

def get_temp_function_name(id_require, id_assert, id_function):
    return str(id_require) + "x" + str(id_assert) + "x" + str(id_function)

def output_transitions_function(precondition_require, function, precondition_assert, id_function, extra_condition_pre, extra_condition_post, config_variables):
    if config_variables.mode == Mode.requires:
        function_precondition = config_variables.functionPreconditions[id_function]
    else:
        function_precondition = "true"
    extra_condition_output_pre = get_extra_condition_output(extra_condition_pre)
    echidna_function_output = (
        "\t\trequire("+ precondition_require + ");\n"
        + "\t\trequire(" + function_precondition + ");\n"
        + "\t\t" + extra_condition_output_pre
        + "\t\t" + function + "\n"
        + "\t\tassert(!(" + precondition_assert + "&& " + extra_condition_post + "));"
    )
    return echidna_function_output

def output_init_function(precondition_assert, extra_condition):
    extra_condition_output = get_extra_condition_output(extra_condition)
    echidna_function_output = extra_condition_output + "\t\tassert(!(" + precondition_assert + "));"
    return echidna_function_output

def get_extra_condition_output(condition):
    extra_condition_output = ""
    if condition != "" and condition != None:
        extra_condition_output = "require(" + condition + ");\n"
    return extra_condition_output

def calculate_optimal_splits(queries_count):
    # Very small contracts - minimal overhead justifies minimal splitting. Execution time is already fast, splitting overhead not worth it.
    # Small-medium contracts - prioritize exploration capacity. Still fast enough that we can afford more splits for better coverage.
    # Large contracts - balanced approach. Start caring about efficiency but still benefit from parallel exploration.
    # Very large contracts - Target ~100 queries per contract, rounded to nearest power of 2. Time becomes the limiting factor, optimize for speed.
    if queries_count < 100:
        return 2
    elif queries_count < 500:
        return 8
    elif queries_count < 1500:
        return 16
    else:
        target_queries_per_split = 100
        ideal_splits = queries_count / target_queries_per_split
        power = round(math.log2(ideal_splits))
        # Clamp between reasonable bounds (16 to 128)
        power = max(4, min(7, power))  # 2^4=16 to 2^7=128
        
        return 2 ** power
