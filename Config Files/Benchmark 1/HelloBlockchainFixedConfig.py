fileName = "HelloBlockchainFixed.sol"
contractName = "HelloBlockchain"
functions = ["SendRequest(requestMessage);", "SendResponse(responseMessage);"]
statePreconditions = ["State == StateType.Respond", "State == StateType.Request"]
functionPreconditions = ["msg.sender == Requestor", "true"]
functionVariables = "uint requestMessage, uint responseMessage"

statesModeState = [[1,0], [0,2]]
statesNamesModeState = ["Request", "Respond"]
statePreconditionsModeState = ["State == StateType.Request", "State == StateType.Respond"]