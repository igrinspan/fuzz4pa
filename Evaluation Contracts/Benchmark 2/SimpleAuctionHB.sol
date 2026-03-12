pragma solidity >=0.4.25 <0.9.0;

contract SimpleAuction {
    uint public auctionStart;
    uint public biddingTime;
    address public highestBidder;
    uint public highestBid;
    bool ended;
    address public _A;
    bool public _hasA;

    mapping(address => uint) pendingReturns;
    uint pendingReturnsCount; // Added.

    event HighestBidIncreased(address bidder, uint amount);
    event AuctionEnded(address winner, uint amount);

    address payable _beneficiary = payable(address(0xb23397f97715118532c8c1207F5678Ed4FbaEA6c));
    address payable beneficiary;
    uint time;
    
    constructor(uint _time, uint _biddingTime, address A) public{
        beneficiary = _beneficiary;
        time = _time;
        auctionStart = 1;
        biddingTime = _biddingTime;
        _A = address(0x10000); // En una de esas hardcodear 0x3000 o alguno de esos que son los que usa Echidna
    }

    function bid() public payable {
        require(time <= (auctionStart + biddingTime));
        require(msg.value > highestBid);

        if (highestBidder != address(0x0)) {
            if (pendingReturns[highestBidder] == 0){
                pendingReturnsCount++;
                if (highestBidder == _A) {
                    _hasA = true;
                }
            }
            pendingReturns[highestBidder] += highestBid;
        }
        highestBidder = msg.sender;
        highestBid = msg.value;
        emit HighestBidIncreased(msg.sender, msg.value);
        t();
    }

    function withdrawA() public returns (bool) {
        require(pendingReturnsCount > 0);
        require(_hasA);
        require(msg.sender == _A);
        uint amount = pendingReturns[msg.sender];
        if (amount > 0) {
            pendingReturns[msg.sender] = 0;
            pendingReturnsCount = pendingReturnsCount - 1;
            _hasA = false;

            if (!payable(msg.sender).send(amount)) {
                pendingReturns[msg.sender] = amount;
                return false;
            }
        }
        t();
        return true;
    }

    function withdrawOther() public returns (bool) {
        require(pendingReturnsCount > 0 && (!_hasA || pendingReturnsCount > 1));
        require(msg.sender != _A);
        uint amount = pendingReturns[msg.sender];
        if (amount > 0) {

            pendingReturns[msg.sender] = 0;
            pendingReturnsCount = pendingReturnsCount - 1;

            if (!payable(msg.sender).send(amount)) {
                pendingReturns[msg.sender] = amount;
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
        require(time >= (auctionStart + biddingTime)); // auction did not yet end
        require(!ended); // this function has already been called
        // 2. Effects
        ended = true;
        emit AuctionEnded(highestBidder, highestBid);

        // 3. Interaction
        beneficiary.transfer(highestBid);
        t();
    }

    function t() internal {
        time = time + 1;
    }
}