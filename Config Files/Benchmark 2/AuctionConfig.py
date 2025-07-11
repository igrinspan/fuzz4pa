fileName = "Auction.sol"
contractName = "Auction"

functions = [
    "Bid();",
    "Withdraw();",
    "AuctionEnd();",
]
statePreconditions = [
    "(!ended && (auctionStart + biddingTime) >= blockNumber)",
    "pendingReturnsCount > 0",
    "(ended && blockNumber > (auctionStart + biddingTime))",
]
functionPreconditions = [
    "msg.value > highestBid",
    "pendingReturns[msg.sender] != 0",
    "true",
]

functionVariables = ""

statesModeState = []
statesNamesModeState = []
statePreconditionsModeState = []
