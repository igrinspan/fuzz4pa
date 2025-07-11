fileName = "BasicProvenanceFixed.sol"
contractName = "BasicProvenance"

functions = ["TransferResponsibility(newCounterparty);", "Complete();"]
functionPreconditions = ["Counterparty == msg.sender", "SupplyChainOwner == msg.sender"]

functionVariables = "address newCounterparty"

statesModeState = [[1,0,0], [0,2,0],[0,0,3]]
statesNamesModeState = ["Created", "InTransit", "Completed"]
statePreconditionsModeState = ["State == StateType.Created", "State == StateType.InTransit", "State == StateType.Completed"]
statePreconditions = ["State != StateType.Completed", "(State != StateType.Completed && State != StateType.Created)"]

