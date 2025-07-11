fileName = "RefundEscrow.sol"
contractName = "RefundEscrow"

functions = [
    "deposit(refundee);",
    "close();",
    "enableRefunds();",
    "beneficiaryWithdraw();",
    "withdraw(payee);",
    "transferPrimary(recipient);"
]
statePreconditions = [
    "_state == State.Active",
    "_state == State.Active",
    "_state == State.Active",
    "_state == State.Closed && address(this).balance > 0",
    "_state == State.Refunding && depositsCount > 0",
    "true"
]
functionPreconditions = [
    "msg.sender == _primary",
    "msg.sender == _primary",
    "msg.sender == _primary",
    "true",
    "_deposits[payee] > 0",
    "recipient != address(0) && msg.sender == _primary"
]
functionVariables = "address refundee, address payable payee, address recipient"

statesModeState = [[1,0,0], [0,2,0], [0,0,3]]
statesNamesModeState = ["Active", "Refunding", "Close"]
statePreconditionsModeState = [
    "_state == State.Active", 
    "_state == State.Refunding", 
    "_state == State.Closed", 
]
