fileName = "Crowdfunding.sol"
contractName = "Crowdfunding"

functions = [
    "Donate(n);",
    "GetFunds(p);",
    "Claim(q);",
]

statePreconditions = [
    "(max_block > blockNumber)",
    "(max_block < blockNumber && goal <= address(this).balance)",
    "(blockNumber > max_block && !funded && goal > address(this).balance && backersCount > 0)",
]
functionPreconditions = [
    "backers[msg.sender] == 0",
    "msg.sender == owner",
    "backers[msg.sender] != 0",
]

functionVariables = "uint256 n, uint256 p, uint256 q"

statesModeState = [[1,0,0,0,0], [0,2,0,0,0], [0,0,3,0,0], [0,0,0,4,0], [0,0,0,0,5]]
statesNamesModeState = ["Empty (without balance)", "Empty (with balance)", "Donate", "Funds", "Claim"]
statePreconditionsModeState = [
    "(!(max_block > blockNumber) && !(max_block < blockNumber && goal <= address(this).balance) && !(blockNumber > max_block && !funded && goal > address(this).balance && backersCount > 0) && address(this).balance == 0)", 
    "(!(max_block > blockNumber) && !(max_block < blockNumber && goal <= address(this).balance) && !(blockNumber > max_block && !funded && goal > address(this).balance && backersCount > 0) && address(this).balance > 0)", 
    "(max_block > blockNumber) && !(max_block < blockNumber && goal <= address(this).balance) && !(blockNumber > max_block && !funded && goal > address(this).balance && backersCount > 0)", 
    "!(max_block > blockNumber) && (max_block < blockNumber && goal <= address(this).balance) && !(blockNumber > max_block && !funded && goal > address(this).balance && backersCount > 0)",
    "!(max_block > blockNumber) && !(max_block < blockNumber && goal <= address(this).balance) && (blockNumber > max_block && !funded && goal > address(this).balance && backersCount > 0)",
]

