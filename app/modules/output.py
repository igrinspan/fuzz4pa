import graphviz
from modules.contract_config import Mode

class Graph:
    def __init__(self, config_variables):
        self.graph = graphviz.Digraph(comment=config_variables.contractName)
        self.dir = config_variables.dir
        self.config_variables = config_variables
        self.nodes = set()  # Track unique nodes
        self.edges = set()  # Track unique edges

    def build_graph(self, init_tests_that_failed, transition_tests_that_failed):
        self.add_failed_tests_init(init_tests_that_failed)
        self.add_failed_tests_transition(transition_tests_that_failed)
        self.graph.render(
            f"{self.dir}/graph/{self.config_variables.contractName}_{self.config_variables.mode}"
        )

        return self

    # Private methods
    def add_failed_tests_init(self, tests_that_failed):
        for test in tests_that_failed:
            parameters = test[0]
            result = test[1]
            self.add_init_node_to_graph(parameters, result)

    def add_failed_tests_transition(self, tests_that_failed):
        for test in tests_that_failed:
            parameters = test[0]
            result = test[1]
            self.add_node_to_graph(
                parameters[0],
                parameters[1],
                parameters[2],
                self.config_variables.states,
                result,
            )

    def add_node_to_graph(
        self,
        id_precondition_require,
        id_precondition_assert,
        id_function,
        states,
        result,
    ):

        source_node_id = combination_to_string(states[id_precondition_require])
        source_node_label = output_combination(id_precondition_require, states, self.config_variables)
        dest_node_id = combination_to_string(states[id_precondition_assert])
        dest_node_label = output_combination(id_precondition_assert, states, self.config_variables)
        
        # Track unique nodes
        self.nodes.add(source_node_id)
        self.nodes.add(dest_node_id)
        
        self.graph.node(  # Nodo fuente
            source_node_id,
            source_node_label,
        )
        self.graph.node(  # Nodo destino
            dest_node_id,
            dest_node_label,
        )
        if not self.config_variables.functions[id_function].startswith("dummy_"):
            if self.config_variables.debug:
                print(f"Adding edge {self.config_variables.functions[id_function]} {result}")
            
            edge_label = f"{self.config_variables.functions[id_function]} {result}"
            # Track unique edges (from_node, to_node, label)
            self.edges.add((source_node_id, dest_node_id, edge_label))
            
            self.graph.edge(  # Eje
                source_node_id,
                dest_node_id,
                label=edge_label,
            )
        else:
            if self.config_variables.debug:
                print(f"DUMMY: No agregamos el eje {self.config_variables.functions[id_function]} {result}")

    def add_init_node_to_graph(self, init_test, result):
        id_precondition_assert = init_test[0]
        init_node_id = "init"
        dest_node_id = combination_to_string(self.config_variables.states[id_precondition_assert])
        dest_node_label = output_combination(
            id_precondition_assert,
            self.config_variables.states,
            self.config_variables,
        )
        
        # Track unique nodes
        self.nodes.add(init_node_id)
        self.nodes.add(dest_node_id)
        
        # Track unique edge
        edge_label = f"constructor {result}"
        self.edges.add((init_node_id, dest_node_id, edge_label))
        
        self.graph.node(init_node_id, init_node_id)
        self.graph.node(
            dest_node_id,
            dest_node_label,
        )
        self.graph.edge(
            init_node_id,
            dest_node_id,
            edge_label,
        )

class OutputPrinter:
    """Prints execution results to console."""

    def __init__(self, config_variables):
        self.directory = config_variables.dir
        self.config_variables = config_variables

    def print_results(self, transition_tests_that_failed, init_tests_that_failed):
        """Imprime por consola los estados a los que podemos llegar desde el constructor
        y los estados a los que podemos llegar desde cada estado."""
        self.print_failed_tests(init_tests_that_failed, True)
        self.print_failed_tests(transition_tests_that_failed)

    # Private methods
    def print_failed_tests(self, tests_that_failed, init=False):
        if init:
            for test in tests_that_failed:
                state = output_combination(test[0][0], self.config_variables.states, self.config_variables)
                print(f"From constructor, it can reach: {state}")
                print("─" * 40)
        else:
            for test in tests_that_failed:
                require = test[0][0]
                assertion = test[0][1]
                function = test[0][2]
                self.print_output(require, function, assertion)

    def print_output(self, id_prec_require, id_function, id_prec_assert):
        combinations = self.config_variables.states
        
        from_state = output_combination(id_prec_require, combinations, self.config_variables)
        function_name = self.config_variables.functions[id_function]
        to_state = output_combination(id_prec_assert, combinations, self.config_variables)
        
        print(f"From state: {from_state}")
        print(f"Doing: {function_name}")
        print(f"Reaches state: {to_state}")
        print("─" * 40)

def combination_to_string(combination):
    output = ""
    for i in combination:
        output += str(i) + "-"
    return output

def output_combination(idx_combination, many_combinations, config_variables):
    combination = many_combinations[idx_combination]
    
    if not any(combination):
        return "Empty"
    
    output_parts = []
    for function in combination:
        if function != 0:
            if config_variables.mode == Mode.requires:
                output_parts.append(config_variables.functions[function - 1])
            else:
                output_parts.append(config_variables.statesNames[function - 1])
    
    # returns Empty when combination is [0, 0, 0, ...]
    # meaning there's no enabled function based on their statePreconditions
    # (does not use functionPreconditions)
    return " ".join(output_parts) if output_parts else "Empty"

