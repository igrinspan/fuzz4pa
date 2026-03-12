fileName = "DefectiveComponentCounter.sol"
contractName = "DefectiveComponentCounter"

functions = ["ComputeTotal();"]
statePreconditions = ["true"]
functionPreconditions = ["Manufacturer == msg.sender"]

functionVariables = ""

statesModeState = [[1,0], [0,2]]
statesNamesModeState = ["Create", "ComputeTotal"]
statePreconditionsModeState = ["State == StateType.Create", "State == StateType.ComputeTotal"]
