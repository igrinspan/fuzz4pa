pragma solidity >=0.4.25 <0.9.0;

contract SimpleAuction {
    uint public auctionStart;
    uint public biddingTime;
    address public highestBidder;
    uint public highestBid;
    bool ended;

    mapping(address => uint) pendingReturns;
    uint pendingReturnsCount; // Added.

    event HighestBidIncreased(address bidder, uint amount);
    event AuctionEnded(address winner, uint amount);
    
    address payable _beneficiary = payable(address(0xb23397f97715118532c8c1207F5678Ed4FbaEA6c));
    address payable beneficiary;
    uint blockNumber;

    constructor(uint _blockNumber, uint _biddingTime) public {
        beneficiary = _beneficiary;
        blockNumber = _blockNumber; 
        auctionStart = 1;
        biddingTime = _biddingTime;
    }

    function bid() public payable {
        require(blockNumber <= (auctionStart + biddingTime));
        require(msg.value > highestBid);

        if (highestBidder != address(0x0)) {
            if (pendingReturns[highestBidder] == 0) {
                pendingReturnsCount++;
            }
            pendingReturns[highestBidder] += highestBid;
        }
        highestBidder = msg.sender;
        highestBid = msg.value;
        emit HighestBidIncreased(msg.sender, msg.value);
        t();
    }

    function withdraw() public returns (bool) {
        require(pendingReturnsCount > 0);
        uint amount = pendingReturns[msg.sender];
        if (amount > 0) {
            pendingReturns[msg.sender] = 0;
            pendingReturnsCount--;

            if (!payable(msg.sender).send(amount)) { // added payable
                pendingReturns[msg.sender] = amount;
                pendingReturnsCount++;
                return false;
            }
        }
        t();
        return true;        
    }

    function auctionEndTime() public view returns (uint256) {
        return auctionStart + biddingTime;
    }
    
    function auctionEnd() public {
        // 1. Conditions
        require(blockNumber >= (auctionStart + biddingTime)); // auction did not yet end
        require(!ended); // this function has already been called

        // 2. Effects
        ended = true;
        emit AuctionEnded(highestBidder, highestBid);

        // 3. Interaction
        beneficiary.transfer(highestBid);
        t();
    }

    function t() internal {
        blockNumber = blockNumber + 1;
    }
}