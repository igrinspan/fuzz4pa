from dataclasses import dataclass
from enum import Enum
import itertools

# Classes:
# - Mode (requires or enumeration)
# - ConfigImporter: takes the ContractConfig and saves all the necessary data for execution in a ConfigVariables type object.
# - ConfigVariables

class Mode(Enum):
    requires = "requires" # Also known as EPA mode (enabledness-preserving abstraction)
    enumeration = "enumeration" # Also known as States mode

class ConfigImporter:
    """ Importa las variables del ContractConfig y las pepara según si estamos en 
    modo requires o enumeration """
    def __init__(self, contract_config_file, config_variables_object, optimizations):
        self.contract_config_file = contract_config_file
        self.config_variables = config_variables_object
        self.optimizations = optimizations

    def config_variables_setup(self, mode):
        """ Traemos los datos del archivo Config del contrato que vamos a analizar y 
        los preparamos (seteamos states, preconditions, extraconditions) según el modo."""
        self.import_config_variables()  # es lo mismo que el make_global_variables.

        funciones_numeros = list(range(1, len(self.config_variables.functions) + 1))
        self.prepare_variables(mode, funciones_numeros)
        self.config_variables.mode = mode

        return self.config_variables

    # Private methods
    def import_config_variables(self):
        c = self.contract_config_file
        
        # Always required variables
        self.config_variables.fileName = "Contracts/" + c.fileName
        self.config_variables.contractFileName = c.fileName
        self.config_variables.functions = c.functions
        self.config_variables.contractName = c.contractName
        self.config_variables.functionVariables = c.functionVariables
        
        # Optional variables for states mode
        try:
            self.config_variables.statesNames = c.statesNamesModeState
        except AttributeError:
            self.config_variables.statesNames = []
        
        # Optional variables for EPA mode
        try:
            self.config_variables.statePreconditions = c.statePreconditions
        except AttributeError:
            self.config_variables.statePreconditions = []
            
        try:
            self.config_variables.functionPreconditions = c.functionPreconditions
        except AttributeError:
            self.config_variables.functionPreconditions = []

    # Se ejecuta en el main para cargar las variables preconditions, states y extraConditions, dependiendo del modo.
    def prepare_variables(self, mode, funciones_numeros):
        if mode == Mode.requires:
            self.update_variables_for_epa_mode(funciones_numeros)
        else:
            self.update_variables_for_states_mode()

    def update_variables_for_epa_mode(self, funciones_numeros):
        self.config_variables.states = self.getCombinations(funciones_numeros)
        self.config_variables.preconditions = self.getPreconditions(funciones_numeros)
        try:
            self.config_variables.extraConditions = [
                self.contract_config_file.epaExtraConditions for _ in range(len(self.config_variables.states))
            ]
        except AttributeError:
            self.config_variables.extraConditions = ["true" for _ in range(len(self.config_variables.states))]

    def update_variables_for_states_mode(self):
        try:
            self.config_variables.preconditions = self.contract_config_file.statePreconditionsModeState
        except AttributeError:
            self.config_variables.preconditions = []
            
        try:
            self.config_variables.states = self.contract_config_file.statesModeState
        except AttributeError:
            self.config_variables.states = []
            
        try:
            self.config_variables.extraConditions = self.contract_config_file.statesExtraConditions
        except AttributeError:
            self.config_variables.extraConditions = ["true" for _ in range(len(self.config_variables.states))]

    def getCombinations(self, funciones_numeros):
        truePreconditions = []
        results = []
        statesTemp = []
        count = len(funciones_numeros)
        for index, statePrecondition in enumerate(self.config_variables.statePreconditions):
            if statePrecondition == "true":
                truePreconditions.append(index + 1)

        # Combinations
        for L in range(len(funciones_numeros) + 1):
            for subset in itertools.combinations(funciones_numeros, L):
                if self.optimizations.reduce_true: # Optimización reduce_true
                    is_true = True
                    for true_pre in truePreconditions:
                        if true_pre not in subset:
                            is_true = False
                    if is_true:
                        results.append(subset)
                else:
                    results.append(subset)
        for partialResult in results:
            paddingResult = []
            paddingResult = [0 for i in range(count)]
            for i in range(count):
                if len(partialResult) > i and partialResult[i] >= 0:
                    indice = partialResult[i]
                    paddingResult[indice - 1] = indice
            statesTemp.append(paddingResult)
        statesTemp2 = []

        # Sacamos estados en los que haya una función i y no haya otra función j tales que precondition[i] = precondition[j].
        if self.optimizations.reduce_equal: # Optimización reduce_equal
            for combination in statesTemp:
                isCorrect = True
                for iNumber, number in enumerate(combination):
                    for idx, x in enumerate(self.config_variables.statePreconditions):
                        if iNumber != idx:
                            if number == 0:
                                if self.config_variables.statePreconditions[iNumber] == x and combination[idx] != 0:
                                    isCorrect = False
                            elif self.config_variables.statePreconditions[iNumber] == x and not((idx+1) in combination):
                                isCorrect = False
                
                if isCorrect:
                    statesTemp2.append(combination)
        else:
            statesTemp2 = statesTemp

        return statesTemp2

    def getPreconditions(self, funciones_numeros):
        preconditions = []
        for result in self.config_variables.states:
            precondition = ""
            for number in funciones_numeros:
                if precondition != "":
                    precondition += " && "
                if number in result:
                    precondition += self.config_variables.statePreconditions[number - 1]
                else:
                    precondition += "!(" + self.config_variables.statePreconditions[number - 1] + ")"
            preconditions.append(precondition)
        return preconditions

@dataclass
class ConfigVariables:
    states: list = None
    preconditions: list = None
    extraConditions: list = None
    functions: list = None
    functionVariables: list = None
    functionPreconditions: list = None
    contractName: str = None
    contractFileName: str = None
    fileName: str = None
    statePreconditions: list = None
    statesNames: list = None

    dir: str = None
    dir_name: str = None
    mode: Mode = None

    debug: bool = False
