pragma solidity >=0.4.25 <0.9.0;

// bugs:
// 1. Auction can never end
// 2. highest bidder can never be refunded their highest bid

// fixes for 0.8.0:
// address(0x0) -> payable(address(0x0))
// msg.sender -> payable(msg.sender)

// For time manipulation:
// added uint blockNumber variable. set in constructor.
// added t() function to increment blockNumber.
// replaced block.number with blockNumber in all places.

contract Auction {
    uint auctionStart;
    uint biddingTime;
    address payable beneficiary;

    bool ended = false;
    address payable highestBidder = payable(address(0));
    uint highestBid = 0;
    mapping(address => uint) pendingReturns;
    uint pendingReturnsCount; // Added this, to match Alloy's analysis.
    uint blockNumber;

    constructor(uint _auctionStart, uint _biddingTime, address payable _beneficiary, uint _blockNumber) public {
        auctionStart = _auctionStart;
        biddingTime = _biddingTime;
        beneficiary = _beneficiary;
        blockNumber = _blockNumber;
    }

    function Bid() public payable {
        uint end = auctionStart + biddingTime;
        require(end >= blockNumber && !ended);
        require(msg.value > highestBid);
        
        pendingReturns[highestBidder] += highestBid;
        pendingReturnsCount++; // Added
        highestBidder = payable(msg.sender);
        highestBid = msg.value;
        t();
    }

    function Withdraw() public {
        require(pendingReturnsCount > 0); // Added
        require(pendingReturns[msg.sender] != 0);

        uint pr = pendingReturns[msg.sender];
        pendingReturns[msg.sender] = 0;
        pendingReturnsCount--; // Added
        payable(msg.sender).transfer(pr);
        t();
    }

    function AuctionEnd() public {
        uint end = auctionStart + biddingTime;
        require(blockNumber > end && ended); // ended is a bug
        
        ended = true;
        beneficiary.transfer(highestBid);
        t();
    }

    function t() internal {
        blockNumber = blockNumber + 1;
    }
}