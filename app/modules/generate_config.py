import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

"""
Module for generating configuration files for SmartAbstractor.

This module parses Solidity contracts to extract relevant information such as function signatures,
state variables, Enums, and preconditions (requires, if-reverts). It then generates a configuration
file (currently in Python format) used by the optimization and abstraction tools.

This works either for EPA mode or for ENUM mode. Not for regular states mode since
that one requires the user to input their predicates.

Key Components:
- SolidityParser: Parses Solidity source code using Regex.
- ConfigGenerator: Formats extracted data into a configuration file.
- ContractAnalyzer: Orchestrates the parsing and generation process.
"""

# TODO (ALREADY DONE): Implement the config generator in States mode for contracts with enums.
# - Identify an enum called 'State' or similar. In all B1 contracts, its called StateType.
# Other names such as State and AuctionState appear in EscrowVault/RefundEscrow and ValidatorAuction respectively.
# Careful in case there is an enum with a similar name that does not represent the state of the contract.
# Also, state variables could have similar names. For example _state, state and auctionState.
# So we should be able to distinguish between the variable that represents the state of the contract and the type of that variable (the enum).
# - Other than identifying the enum, we also need to identify the variable that represents the state of the contract. It should be of the type of that enum.
# - For each value of the State enum, generate a state and a precondition for that state like "State == StateType.Requested".
# - Expected variables of the config file for reference (for example SimpleMarketplaceFixed here):
# statesModeState = [[1,0,0], [0,2,0],[0,0,3]]
# statesNamesModeState = ["ItemAvailable", "OfferPlaced", "Accepted"]
# statePreconditionsModeState = ["State == StateType.ItemAvailable", "State == StateType.OfferPlaced", "State == StateType.Accepted"]

class RegexPatterns:
    """
    Collection of Regex patterns used to parse Solidity contracts.
    
    Attributes:
        CONTRACT_NAME (str): Regex to match contract definition, handling inheritance.
        FUNCTION_SIGNATURE (str): Regex to match function headers.
        PARAMETER (str): Regex to match function parameters.
        REQUIRES (str): Regex to match 'require' statements.
        IF_REVERTS (str): Regex to match 'if (...) revert();' patterns.
        IF_ELSE_REVERTS (str): Regex to match if-else blocks where one branch reverts.
        STATE_ENUM (str): Regex to match Enum definitions for state.
        STATE_VARIABLE (str): Regex to match the state variable declaration.
    """
    CONTRACT_NAME = r"contract\s+(\w+)[^{]*\{"
    FUNCTION_SIGNATURE = r"function[ \t]+(\w+)\s*\(([^)]*)\)\s*(public|private|external|internal)?\s*(pure|view|payable)?\s*(returns\s*\([^)]+\))?"
    # Support types with multiple words (e.g., 'address payable', 'uint256', 'string memory', etc.)
    PARAMETER = r"([\w\s]+(?:\[\])?)\s*(memory|storage|calldata)?\s+(\w+)"
    REQUIRES = r"require\s*\(\s*(.*?)(?:\s*,\s*\".*?\")?\s*\)\s*;"
    IF_REVERTS = r"if\s*\(\s*(.*?)\s*\)\s*{?\s*revert\s*\(\s*\)\s*;?\s*}?"
    IF_ELSE_REVERTS = r"if\s*\(\s*(.*)\s*\)\s*\{[^}]*\}\s*else\s*\{\s*revert\(\s*\)\s*;?\s*\}"
    STATE_ENUM = r"enum\s+(\w*(?:State|StateType)\w*)\s*\{([^}]+)\}"
    STATE_VARIABLE = r"(\w*(?:State|StateType)\w*)\s+(?:public|private|internal|external)?\s*(\w+)(?:\s*=|;)"
    INHERITANCE = r"contract\s+\w+\s+is\s+([\w,\s]+)\s*[{]"
    
    @classmethod
    def get_all(cls) -> Dict[str, str]:
        """Returns a dictionary of all regex patterns."""
        return {
            "contract_name": cls.CONTRACT_NAME,
            "function_signature": cls.FUNCTION_SIGNATURE,
            "parameter": cls.PARAMETER,
            "requires": cls.REQUIRES,
            "if_reverts": cls.IF_REVERTS,
            "if_else_reverts": cls.IF_ELSE_REVERTS,
            "state_enum": cls.STATE_ENUM,
            "state_variable": cls.STATE_VARIABLE,
            "inheritance": cls.INHERITANCE
        }

@dataclass
class FunctionData:
    """
    Data structure to hold information extracted from a Solidity function.
    
    Attributes:
        name (str): Full function signature (e.g., "MetaCoin(address caller)").
        parameters (List[str]): List of parameters with types.
        visibility (str): Function visibility (public, external, etc.).
        requires_state (List[str]): Preconditions dependent on state variables.
        requires_function (List[str]): Preconditions dependent on function arguments/msg/tx.
        if_reverts_state (List[str]): 'if' conditions that lead to revert (state-dependent).
        if_reverts_function (List[str]): 'if' conditions that lead to revert (function-dependent).
        statePreconditions (List[str]): Unified list of state-based preconditions.
        functionPreconditions (List[str]): Unified list of function-based preconditions.
    """
    name: str
    parameters: List[str] = field(default_factory=list)
    visibility: str = "public"
    requires_state: List[str] = field(default_factory=list)
    requires_function: List[str] = field(default_factory=list)
    if_reverts_state: List[str] = field(default_factory=list)
    if_reverts_function: List[str] = field(default_factory=list)
    if_else_reverts_state: List[str] = field(default_factory=list)
    if_else_reverts_function: List[str] = field(default_factory=list)
    statePreconditions: List[str] = field(default_factory=list)
    functionPreconditions: List[str] = field(default_factory=list)
    
    def unify_clauses(self, clause_type: str) -> None:
        """
        Unify all preconditions of a specific type (state or function) into a single list.
        
        Args:
            clause_type (str): 'state' or 'function'.
        """
        if not getattr(self, f"requires_{clause_type}") and \
           not getattr(self, f"if_reverts_{clause_type}") and \
           not getattr(self, f"if_else_reverts_{clause_type}"):
            getattr(self, f"{clause_type}Preconditions").append("true")
        else:
            setattr(
                self, 
                f"{clause_type}Preconditions", 
                getattr(self, f"requires_{clause_type}") + 
                getattr(self, f"if_reverts_{clause_type}") + 
                getattr(self, f"if_else_reverts_{clause_type}")
            )

@dataclass
class ContractData:
    """
    Data structure to hold information extracted from the Contract.
    
    Attributes:
        contract_name (str): The name of the contract.
        data (List[FunctionData]): List of function data objects.
        state_enum (str): Name of the Enum type representing the state (if any).
        state_values (List[str]): List of possible values for the state Enum.
        state_variable (str): Name of the state variable of type state_enum.
    """
    contract_name: str
    data: List[FunctionData] = field(default_factory=list)
    state_enum: str = None
    state_values: List[str] = field(default_factory=list)
    state_variable: str = None

class SolidityParser:
    """
    Parser for Solidity source code.
    
    Uses regex patterns to extract contract details, function definitions, and preconditions.
    """
    def __init__(self):
        self.patterns = RegexPatterns.get_all()
    
    def extract_function_body(self, code: str, start_pos: int) -> Tuple[str, int]:
        """
        Extracts the body of a function (or contract) starting from a given position.
        
        Args:
            code (str): The source code string.
            start_pos (int): The index where the search for the opening brace should start.
            
        Returns:
            Tuple[str, int]: A tuple containing the extracted body string (including braces)
                             and the index in the code where the body ends.
        """
        brace_count = 0
        function_body = ""
        i = start_pos
        
        # Find opening brace
        while i < len(code) and code[i] != "{":
            i += 1
        
        if i < len(code):
            function_body += code[i]
            brace_count = 1
            i += 1
        
        # Iterate through the code until all braces are closed
        while i < len(code) and brace_count > 0:
            char = code[i]
            function_body += char
            
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            
            i += 1
        
        return function_body, i
    
    def is_transaction_dependent(self, parameter_names: List[str], clause: str) -> bool:
        """
        Check if a clause is transaction-dependent (i.e., it depends on msg.sender, tx.origin, or any parameter of the function).
        This is to determine if a require clause is a function precondition or a state precondition.
        """
        return any(param in clause for param in parameter_names) or \
               any(keyword in clause for keyword in ["msg.", "tx."])
    
    def extract_modifiers(self, contract_code: str):
        # Matches: modifier name(params) { ... }
        modifier_pattern = r'modifier\s+(\w+)\s*\(([^)]*)\)\s*\{([\s\S]*?)\}'
        modifiers = {}
        for name, params, body in re.findall(modifier_pattern, contract_code, re.DOTALL):
            param_names = [p.strip().split()[-1] for p in params.split(',') if p.strip()]
            # Extract require clauses from the modifier body
            require_pattern = r'require\s*\((.*?)\)\s*;'
            requires = re.findall(require_pattern, body, re.DOTALL)
            modifiers[name] = {
                'params': param_names,
                'requires': requires
            }
        return modifiers

    def extract_function_modifiers(self, contract_code):
        # Matches: function name(...) ... modifier1 ... modifier2(...) ...
        func_pattern = r'function\s+\w+\s*\([^\)]*\)\s*(?:public|private|external|internal)?(?:\s*\w+)*\s*((?:\w+\s*(?:\([^\)]*\))?\s*)*)\{'
        func_modifiers = []
        for match in re.finditer(func_pattern, contract_code):
            modifier_str = match.group(1).strip()
            # Split by spaces, but keep arguments together
            mods = re.findall(r'(\w+\s*(?:\([^\)]*\))?)', modifier_str)
            func_modifiers.append(mods)
        return func_modifiers

    def _parse_functions_from_body(self, body: str, modifs: dict) -> List[FunctionData]:
        """
        Parse all public/external non-view/pure functions from a contract body.

        Args:
            body (str): The full text of the contract body (including braces).
            modifs (dict): Pre-extracted modifier definitions from the whole file.

        Returns:
            List[FunctionData]: Parsed function data objects.
        """
        functions = []
        for match in re.finditer(self.patterns["function_signature"], body):
            function_name, parameters, visibility, func_type, returns = match.groups()

            # Skip non-public/external functions
            if visibility not in ("public", "external"):
                continue

            # Skip view and pure functions
            if func_type in ("view", "pure"):
                continue

            # Collect modifiers declared between the signature end and the opening brace
            sig_end = match.end()
            modifier_text = ""
            i = sig_end
            while i < len(body) and body[i] != "{":
                modifier_text += body[i]
                i += 1

            known_keywords = {"public", "private", "external", "internal", "view", "pure", "payable", "returns", ""}
            mod_matches = re.findall(r"(\w+)(?:\s*\(([^)]*)\))?", modifier_text)
            function_modifiers = [
                (mod_name, mod_args)
                for mod_name, mod_args in mod_matches
                if mod_name not in known_keywords
            ]
            if function_modifiers:
                print(f"Function '{function_name}' has modifiers: {function_modifiers}")

            # Extract parameter info
            parameter_names = []
            parameters_names_types = []
            for param_match in re.finditer(self.patterns["parameter"], parameters):
                param_type, storage_type, param_name = param_match.groups()
                parameter_names.append(param_name)
                if storage_type:
                    parameters_names_types.append(f"{param_type} {storage_type} {param_name}")
                else:
                    parameters_names_types.append(f"{param_type} {param_name}")

            full_function_name = f"{function_name}({', '.join(parameter_names)})"
            function_body, _ = self.extract_function_body(body, match.end())

            # Inline modifier requires into function body
            modifier_requires = []
            for mod_name, mod_args in function_modifiers:
                if mod_name in modifs:
                    mod = modifs[mod_name]
                    mod_params = mod["params"]
                    mod_requires = mod["requires"]
                    arg_values = [a.strip() for a in mod_args.split(",")] if mod_args else []
                    param_map = dict(zip(mod_params, arg_values))
                    for req in mod_requires:
                        req_clause = req
                        for param, value in param_map.items():
                            req_clause = re.sub(rf"\b{re.escape(param)}\b", value, req_clause)
                        modifier_requires.append(f"require({req_clause});")

            modifier_requires_str = "\n".join(modifier_requires)
            if modifier_requires:
                brace_index = function_body.find("{")
                if brace_index != -1:
                    function_body_with_mods = (
                        function_body[:brace_index + 1] + "\n" + modifier_requires_str + "\n" + function_body[brace_index + 1:]
                    )
                else:
                    function_body_with_mods = modifier_requires_str + "\n" + function_body
            else:
                function_body_with_mods = function_body

            function_data = FunctionData(
                name=full_function_name,
                parameters=parameters_names_types,
                visibility=visibility
            )

            for pattern_key in ["requires", "if_reverts", "if_else_reverts"]:
                self.extract_and_categorize_clauses(
                    pattern_key, function_body_with_mods, parameter_names, function_data
                )

            function_data.unify_clauses("state")
            function_data.unify_clauses("function")

            functions.append(function_data)
        return functions

    def extract_and_categorize_clauses(
        self, 
        pattern_key: str, 
        function_body: str, 
        parameter_names: List[str], 
        function_data: FunctionData
    ) -> None:
        """
        Extracts clauses (requires, if-reverts) from the function body and categorizes them.
        
        Clauses are categorized as either 'function' or 'state' preconditions based on whether
        they depend on function parameters/msg/tx or contract state variables.
        
        Args:
            pattern_key (str): The key for the regex pattern to use (e.g., 'requires', 'if_reverts').
            function_body (str): The code of the function body.
            parameter_names (List[str]): List of function parameter names.
            function_data (FunctionData): The data object to populate with extracted clauses.
        """

        flags = re.DOTALL if pattern_key == "requires" else 0
        matches = re.findall(self.patterns[pattern_key], function_body, flags)
        def split_top_level_and(clause):
            # Only split by top-level &&, not inside parentheses
            result = []
            current = ''
            depth = 0
            i = 0
            while i < len(clause):
                if clause[i] == '(':
                    depth += 1
                    current += clause[i]
                elif clause[i] == ')':
                    depth -= 1
                    current += clause[i]
                elif depth == 0 and clause[i:i+2] == '&&':
                    result.append(current.strip())
                    current = ''
                    i += 1  # skip second &
                else:
                    current += clause[i]
                i += 1
            if current.strip():
                result.append(current.strip())
            return result
        
        def inline_local_assignments(function_body, require_clause):
            # Find simple assignments: uint end = auctionStart + biddingTime;
            assignments = dict(re.findall(r'^\s*\w+\s+(\w+)\s*=\s*([^;]+);', function_body, re.MULTILINE))
            # Replace local variable in require clause with its assignment
            for var, expr in assignments.items():
                # Use word boundaries to avoid partial replacements
                require_clause = re.sub(rf'\b{re.escape(var)}\b', f'({expr})', require_clause)
            return require_clause



        for clause in matches:
            cleaned_clause = clause.strip()

            # Inline local variable assignments in the clause
            cleaned_clause = inline_local_assignments(function_body, cleaned_clause)

            # If it is inside of an if-revert, we need to negate it
            if pattern_key == "if_reverts":
                cleaned_clause = f"!({cleaned_clause})"

            # If clause contains '||', do not split
            if '||' in cleaned_clause:
                sub_clauses = [cleaned_clause]
            else:
                sub_clauses = split_top_level_and(cleaned_clause)

            for sub in sub_clauses:
                if not sub:
                    continue
                if self.is_transaction_dependent(parameter_names, sub):
                    getattr(function_data, f"{pattern_key}_function").append(sub)
                else:
                    getattr(function_data, f"{pattern_key}_state").append(sub)
    
    def parse_contract(self, file_path: str) -> ContractData:
        """
        Parses a Solidity file and extracts all relevant contract data.
        
        Handles files with multiple contracts by attempting to find the contract matching the filename.
        Extracts Enums, State Variables, and FunctionDefinitions.
        
        Args:
            file_path (str): The absolute path to the Solidity contract file.
            
        Returns:
            ContractData: An object containing the extracted structure and logic of the contract.
            
        Raises:
            ValueError: If no contracts are found or if the target contract cannot be identified.
        """
        with open(file_path, "r") as contract_file:
            solidity_code = contract_file.read()
        
        # Extract contract name
        # Extract contract name
        target_name = os.path.splitext(os.path.basename(file_path))[0]
        contract_matches = []
        
        for match in re.finditer(self.patterns["contract_name"], solidity_code):
            contract_matches.append((match.group(1), match.end() - 1))

        if not contract_matches:
             raise ValueError("Error: No contracts found in file")
        
        selected_contract = None
        contract_body_start = 0
        
        # Try to find the contract with the same name as the file
        for name, start in contract_matches:
            if name == target_name:
                selected_contract = name
                contract_body_start = start
                break
        
        # If not found and there is only one contract, use that one
        if not selected_contract and len(contract_matches) == 1:
            selected_contract = contract_matches[0][0]
            contract_body_start = contract_matches[0][1]
            
        if not selected_contract:
            available = [n for n, s in contract_matches]
            raise ValueError(f"Error: Multiple contracts found ({available}) and none matches filename '{target_name}'.")

        contract_name = selected_contract
        
        # Extract contract body effectively limiting scope
        contract_body, _ = self.extract_function_body(solidity_code, contract_body_start)
        
        
        functions = []

        # Extract state enum and variable from contract_body
        state_enum_matches = re.findall(self.patterns["state_enum"], contract_body)
        enum_type = None
        enum_values = []
        if state_enum_matches:
            enum_type = state_enum_matches[0][0]
            enum_values = [item.strip() for item in state_enum_matches[0][1].split(",") if item.strip()]
        
        state_variable_matches = re.findall(self.patterns["state_variable"], contract_body)
        state_variable = None
        if state_variable_matches:
             # state_variable_matches is list of tuples (Type, Name)
             # We want the one that matches enum_type
             if enum_type:
                 for v_type, v_name in state_variable_matches:
                     if v_type == enum_type:
                         state_variable = v_name
                         break


        modifs = self.extract_modifiers(solidity_code)

        # Parse functions from the main contract body using the helper
        functions = self._parse_functions_from_body(contract_body, modifs)

        # ------------------------------------------------------------------ #
        # Inheritance: collect public/external functions from parent contracts #
        # ------------------------------------------------------------------ #
        inheritance_pattern = (
            r"contract\s+" + re.escape(contract_name) + r"\s+is\s+([\w,\s]+)\s*[{]"
        )
        inheritance_match = re.search(inheritance_pattern, solidity_code)
        if inheritance_match:
            parent_names = [
                n.strip() for n in inheritance_match.group(1).split(",") if n.strip()
            ]
            print(f"[INFO] Contract '{contract_name}' inherits from: {parent_names}")

            contract_lookup = {name: start for name, start in contract_matches}
            known_function_names = {func.name for func in functions}

            for parent_name in parent_names:
                if parent_name not in contract_lookup:
                    print(f"[WARN] Parent contract '{parent_name}' not found in the same file; skipping.")
                    continue
                parent_start = contract_lookup[parent_name]
                parent_body, _ = self.extract_function_body(solidity_code, parent_start)
                parent_functions = self._parse_functions_from_body(parent_body, modifs)
                for pf in parent_functions:
                    if pf.name not in known_function_names:
                        functions.append(pf)
                        known_function_names.add(pf.name)
                        print(f"[INFO] Inherited function '{pf.name}' from '{parent_name}'.")


        return ContractData(
            contract_name=contract_name,
            data=functions,
            state_enum=enum_type,
            state_values=enum_values,
            state_variable=state_variable
        )

class ConfigGenerator:
    """Generates configuration files for Solidity contracts."""
    
    def __init__(self, contract_file: str, contract_data: ContractData):
        self.contract_file = contract_file
        self.contract_data = contract_data
    
    def _format_precondition(self, preconditions: List[str]) -> str:
        filtered_preconditions = [pre for pre in preconditions if pre != "true"]
        if not filtered_preconditions:
            return "true"
        # Flatten multiline preconditions
        return " && ".join(f"({pre.replace('\n', ' ').replace('\r', ' ').strip()})" for pre in filtered_preconditions)
    
    def _collect_function_variables(self) -> Set[str]:
        function_variables = set()
        for func in self.contract_data.data:
            for param in func.parameters:
                function_variables.add(param)
        return function_variables
    
    def generate_config(self) -> str:
        """
        Generates the content of the configuration file.
        
        Constructs the Python code for the configuration, including:
        - Contract metadata (name, filename)
        - Function lists and preconditions
        - State variable definitions (e.g., statesModeState) for Enum mode.
        
        Returns:
            str: The complete string content of the configuration file.
        """
        config_parts = []
        
        # Filename and contract name
        config_parts.append(f'fileName = "{os.path.basename(self.contract_file)}"')
        config_parts.append(f'contractName = "{self.contract_data.contract_name}"')
        
        # Functions list
        functions_list = [f'    "{func.name};",' for func in self.contract_data.data]
        config_parts.append("functions = [\n" + "\n".join(functions_list) + "\n]")
        
        # State preconditions
        state_preconditions = [
            f'    "{self._format_precondition(func.statePreconditions)}",'
            for func in self.contract_data.data
        ]
        config_parts.append("statePreconditions = [\n" + "\n".join(state_preconditions) + "\n]")
        
        # Function preconditions
        function_preconditions = [
            f'    "{self._format_precondition(func.functionPreconditions)}",'
            for func in self.contract_data.data
        ]
        config_parts.append("functionPreconditions = [\n" + "\n".join(function_preconditions) + "\n]")
        
        # Function variables (sorted for deterministic output)
        function_variables = self._collect_function_variables()
        function_variables = sorted(set(var.strip() for var in function_variables))
        variables_str = ", ".join([v.replace("\n", " ").replace("\r", " ").strip() for v in function_variables])
        config_parts.append(f'functionVariables = "{variables_str}"')
        
        # Extra configuration
        if self.contract_data.state_enum and self.contract_data.state_variable:
            # Generate Enum Mode configuration
            states = []
            statesNames = []
            statePreconditions = []
            
            num_states = len(self.contract_data.state_values)
            
            for index, value in enumerate(self.contract_data.state_values):
                # Construct the state predicate: State == StateType.Value
                predicate = f"{self.contract_data.state_variable} == {self.contract_data.state_enum}.{value}"
                
                statesNames.append(f'"{value}"')
                statePreconditions.append(f'"{predicate}"')
                
                # Generate the diagonal matrix logic: [0, 0, ..., i+1, ..., 0]
                # where the i-th element is index + 1
                state_vector = [0] * num_states
                state_vector[index] = index + 1
                states.append(str(state_vector))

            states_str = ",\n".join(f"    {s}" for s in states)
            config_parts.append(f"statesModeState = [\n{states_str},\n]")
            names_str = ",\n".join(f"    {s}" for s in statesNames)
            config_parts.append(f"statesNamesModeState = [\n{names_str},\n]")
            preconditions_str = ",\n".join(f"    {s}" for s in statePreconditions)
            config_parts.append(f"statePreconditionsModeState = [\n{preconditions_str},\n]")

        else:
            config_parts.append("statesNamesModeState = []")
            config_parts.append("statesModeState = []")
            config_parts.append("statePreconditionsModeState = []")
        
        return "\n\n".join(config_parts)
    
    def write_config_file(self) -> str:
        """
        Writes the generated configuration to a file in the 'Configs' directory.
        
        Returns:
            str: The absolute path to the generated configuration file.
        """
        config_content = self.generate_config()
        base_name = os.path.splitext(self.contract_file)[0]
        config_file_path = f"{base_name}Config.py"

        # TODO: For now, the new config file is written to the same directory as the contract.
        # Instead of it being saved in the Contracts directory, it should be saved in a separate Configs directory.
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Configs")

        config_file_path = os.path.join(config_dir, os.path.basename(config_file_path))
        
        with open(config_file_path, "w") as config_file:
            config_file.write(config_content)
        
        return config_file_path

class _ContractAnalyzer:
    """
    Internal controller for analyzing contracts and generating configurations.
    """
    def __init__(self):
        self.parser = SolidityParser()
    
    def analyze_contract(self, contract_file: str) -> ContractData:
        """
        Analyzes a single contract file.
        
        Args:
            contract_file (str): Path to the contract file (relative to app/Contracts or absolute).
            
        Returns:
            ContractData: Extracted data from the contract.
        """
        # print(f"Analyzing contract: {contract_file}")
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), contract_file)
        # print(f"Current directory: {os.path.dirname(os.path.abspath(__file__))}")
        # print(f"Resolved contract file path: {file_path}")
        contract_data = self.parser.parse_contract(file_path)
        return contract_data
    
    def print_analysis_results(self, contract_data: ContractData) -> None:
        print(f"Contract Name: {contract_data.contract_name}")
        
        for func in contract_data.data:
            print(f"\nFunction Name: {func.name}")
            print(f"  Parameters: {func.parameters}")
            print(f"  State Preconditions: {func.statePreconditions}")
            print(f"  Function Preconditions: {func.functionPreconditions}")
            
        print("\nDetailed Function Data:")
        for func in contract_data.data:
            print(f"\nFunction Name: {func.name}")
            print(f"  Requires State: {func.requires_state}")
            print(f"  Requires Function: {func.requires_function}")
            print(f"  If-Reverts State: {func.if_reverts_state}")
            print(f"  If-Reverts Function: {func.if_reverts_function}")
            print(f"  If-Else-Reverts State: {func.if_else_reverts_state}")
            print(f"  If-Else-Reverts Function: {func.if_else_reverts_function}")
    
    def generate_config(self, contract_file: str, contract_data: ContractData) -> str:
        """
        Generates and writes the configuration file for the analyzed contract.
        
        Args:
            contract_file (str): Path to the source contract file.
            contract_data (ContractData): The data extracted from the analysis.
            
        Returns:
            str: Path to the generated configuration file.
        """
        print(f"[INFO] Generating config for contract: {os.path.basename(contract_file)}")
        # Extract just the filename without directory
        config_generator = ConfigGenerator(contract_file, contract_data)
        return config_generator.write_config_file()


def create_config_file(contract_file_path: str) -> str:
    """
    Analyzes a smart contract and generates a configuration file.

    This function serves as the main entry point for the module. It orchestrates the
    parsing of the Solidity contract and the generation of the Python configuration file.

    Args:
        contract_file_path (str): The absolute or relative path to the Solidity contract file.

    Returns:
        str: The absolute path to the generated configuration file.
    """
    analyzer = _ContractAnalyzer()
    
    # Resolve absolute path if relative
    if not os.path.isabs(contract_file_path):
        contract_file_path = os.path.abspath(contract_file_path)
        
    contract_data = analyzer.analyze_contract(contract_file_path)
    config_path = analyzer.generate_config(contract_file_path, contract_data)
    
    return config_path