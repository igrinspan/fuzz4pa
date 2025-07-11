fileName = "SimpleAuctionHB.sol"
contractName = "SimpleAuction"
functions = [
    "bid();",
    "withdrawA();",
    "withdrawOther();",
    "auctionEnd();",
]
statePreconditions = [
    "time <= (auctionStart + biddingTime)",
    "pendingReturnsCount > 0 && _hasA",
    "pendingReturnsCount > 0 && (!_hasA || pendingReturnsCount > 1)",
    "!ended && time >= (auctionStart + biddingTime)",
]
functionPreconditions = [
    "msg.value > highestBid",
    "true",
    "msg.sender == _A",
    "msg.sender != _A"
]
functionVariables = "address highestBidderA"

statesModeState = [
    [1,0,0,0,0,0], 
    [0,2,0,0,0,0], 
    [0,0,3,0,0,0], 
    [0,0,0,4,0,0], 
    [0,0,0,0,5,0], 
    [0,0,0,0,0,6]
]
statesNamesModeState = [
    "No bids && !ended", 
    "No bids && ended", 
    "HighestBidder = A && !ended", 
    "HighestBidder = A && ended", 
    "HighestBidder != A && !ended", 
    "HighestBidder != A && ended"
]
statePreconditionsModeState = [
    "!ended && highestBidder == address(0x0) && pendingReturnsCount == 0", 
    "ended && highestBidder == address(0x0) && pendingReturnsCount == 0", 
    "!ended && highestBidder != address(0x0) && highestBidder == _A", 
    "ended && highestBidder != address(0x0) && highestBidder == _A",
    "!ended && highestBidder != address(0x0) && highestBidder != _A",
    "ended && highestBidder != address(0x0) && highestBidder != _A",
]
