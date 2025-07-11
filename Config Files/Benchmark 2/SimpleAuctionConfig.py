fileName = "SimpleAuction.sol"
contractName = "SimpleAuction"
functions = [
    "bid();",
    "withdraw();",
    "auctionEnd();",
]

statePreconditions = [
    "blockNumber <= (auctionStart + biddingTime)",
    "pendingReturnsCount > 0",
    "!ended && blockNumber >= (auctionStart + biddingTime)",
]
functionPreconditions = [
    "msg.value > highestBid",
    "true",
    "true",
]
functionVariables = "address refundee"

statesModeState = [
    [1,0,0,0], 
    [0,2,0,0], 
    [0,0,3,0], 
    [0,0,0,4]
]
statesNamesModeState = [
    "Ongoing, no bids made", 
    "Ended without bids", 
    "Ongoing, with bids", 
    "Ended with bids"
]
statePreconditionsModeState = [
    "!ended && highestBidder == address(0x0) && pendingReturnsCount == 0", 
    "ended && highestBidder == address(0x0) && pendingReturnsCount == 0", 
    "!ended && highestBidder != address(0x0)",
    "ended && highestBidder != address(0x0)",
]