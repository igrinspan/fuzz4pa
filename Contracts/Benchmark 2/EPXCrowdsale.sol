pragma solidity >=0.4.25 <0.9.0;

// Added usersEPXfundValueCount variable to track number of contributors. It is updated in buy and refund functions.
// Added t public function to increment blockNumber by n.

contract owned {
  address public owner;

  constructor() {
    owner = msg.sender;
  }
  modifier onlyOwner {
    require(msg.sender == owner);
    _;
  }
}

contract safeMath {
  function safeMul(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a * b;
    safeAssert(a == 0 || c / a == b);
    return c;
  }

  function safeDiv(uint256 a, uint256 b) internal pure returns (uint256) {
    safeAssert(b > 0);
    uint256 c = a / b;
    safeAssert(a == b * c + a % b);
    return c;
  }

  function safeSub(uint256 a, uint256 b) internal pure returns (uint256) {
    safeAssert(b <= a);
    return a - b;
  }

  function safeAdd(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a + b;
    safeAssert(c>=a && c>=b);
    return c;
  }

  function safeAssert(bool assertion) internal pure {
    if (!assertion) revert();
  }
}

abstract contract StandardToken is owned, safeMath {
  function balanceOf(address who) view public virtual returns (uint256);
  function transfer(address to, uint256 value) public virtual returns (bool);
  event Transfer(address indexed from, address indexed to, uint256 value);
}

contract EPXCrowdsale is owned, safeMath {

  address        public admin; // admin address
  StandardToken  public tokenReward; // address of the token used as reward

  // deployment variables for static supply sale
  uint256 private initialTokenSupply;
  uint256 private tokensRemaining;

  // multi-sig addresses and price variable
  address payable beneficiaryWallet;                       
  uint256 public amountRaisedInWei;
  uint256 public fundingMinCapInWei;

  // loop control, ICO startup and limiters
  string  public CurrentStatus                    = "";       // current crowdsale status
  uint256 public fundingStartBlock;                           // crowdsale start block#
  uint256 public fundingEndBlock;                             // crowdsale end block#
  uint256 public blockNumber;                                 
  bool    public isCrowdSaleClosed               = false;     // crowdsale completion boolean
  bool    private areFundsReleasedToBeneficiary  = false;     // boolean for founder to receive Eth or not
  bool    public isCrowdSaleSetup                = false;     // boolean for crowdsale setup

  event Transfer(address indexed from, address indexed to, uint256 value);
  event Approval(address indexed owner, address indexed spender, uint256 value);
  event Buy(address indexed _sender, uint256 _eth, uint256 _EPX);
  event Refund(address indexed _refunder, uint256 _value);
  event Burn(address _from, uint256 _value);

  mapping(address => uint256) balancesArray;
  mapping(address => uint256) usersEPXfundValue;
  uint256 usersEPXfundValueCount;


  constructor(uint256 _blockNumber) public onlyOwner {
    admin = msg.sender;
    CurrentStatus = "Crowdsale deployed to chain";
    blockNumber = _blockNumber;
  }

  // total number of tokens initially
  function initialEPXSupply() public view returns (uint256 initialEPXtokenCount) {
    return safeDiv(initialTokenSupply,uint256(10000)); // div by 10,000 for display normalisation (4 decimals)
  }

  // remaining number of tokens
  function remainingEPXSupply() public view returns (uint256 remainingEPXtokenCount) {
    return safeDiv(tokensRemaining,uint256(10000)); // div by 10,000 for display normalisation (4 decimals)
  }

  // setup the CrowdSale parameters
  function SetupCrowdsale(uint256 _fundingStartBlock, uint256 _fundingEndBlock) public onlyOwner returns (bytes32 response) {
    if ((msg.sender == admin) && !isCrowdSaleSetup && !(beneficiaryWallet != address(0))) {
      // init addresses
      beneficiaryWallet                       = payable(0x7A29e1343c6a107ce78199F1b3a1d2952efd77bA);
      tokenReward                             = StandardToken(0x35BAA72038F127f9f8C8f9B491049f64f377914d);

      // funding targets
      fundingMinCapInWei                      = 30000000000000000000;                       // ETH 300 + 000000000000000000 18 dec wei

      // update values
      amountRaisedInWei                       = 0;
      initialTokenSupply                      = 200000000000;                               // 20,000,000 + 4 dec resolution
      tokensRemaining                         = initialTokenSupply;
      fundingStartBlock                       = _fundingStartBlock;
      fundingEndBlock                         = _fundingEndBlock;

      // configure crowdsale
      isCrowdSaleSetup                        = true;
      isCrowdSaleClosed                       = false;
      CurrentStatus                           = "Crowdsale is setup";
      return "Crowdsale is setup";
    } else if (msg.sender != admin) {
      return "not authorised";
    } else  {
      return "campaign cannot be changed";
    }
  }

  function checkPrice() internal view returns (uint256 currentPriceValue) {
    if (blockNumber >= fundingStartBlock+177534) { // 30-day price change/final 30day change
      return (7600); //30days-end   =7600EPX:1ETH
    } else if (blockNumber >= fundingStartBlock+124274) { //3 week mark/over 21days
      return (8200); //3w-30days    =8200EPX:1ETH
    } else if (blockNumber >= fundingStartBlock) { // start [0 hrs]
      return (8800); //0-3weeks     =8800EPX:1ETH
    }
  }

  receive () external payable {
    buy();
  }
  
  function buy() public payable {
    // 0. conditions (length, crowdsale setup, zero check, exceed funding contrib check, contract valid check, within funding block range check, balance overflow check etc)
    require(!(msg.value == 0) && (blockNumber <= fundingEndBlock) && (blockNumber >= fundingStartBlock) && (tokensRemaining > 0));

    // 1. vars
    uint256 rewardTransferAmount    = 0;

    // 2. effects
    amountRaisedInWei               = safeAdd(amountRaisedInWei, msg.value);
    rewardTransferAmount            = ((safeMul(msg.value, checkPrice())) / 100000000000000);

    // 3. interaction
    tokensRemaining                 = safeSub(tokensRemaining, rewardTransferAmount);
    tokenReward.transfer(msg.sender, rewardTransferAmount);

    // 4. events
    if (usersEPXfundValue[msg.sender] == 0) {
      usersEPXfundValueCount = safeAdd(usersEPXfundValueCount, 1);
    }
    usersEPXfundValue[msg.sender]   = safeAdd(usersEPXfundValue[msg.sender], msg.value);
    emit Buy(msg.sender, msg.value, rewardTransferAmount);
  }

  function beneficiaryMultiSigWithdraw(uint256 _amount) public onlyOwner {
    require(areFundsReleasedToBeneficiary && (amountRaisedInWei >= fundingMinCapInWei));
    beneficiaryWallet.transfer(_amount);
    emit Transfer(address(this), beneficiaryWallet, _amount);
  }

  function checkGoalReached() public onlyOwner { // return crowdfund status to owner for each result case, update public vars
    // update state & status variables
    require (isCrowdSaleSetup);
    if ((amountRaisedInWei < fundingMinCapInWei) && (blockNumber <= fundingEndBlock && blockNumber >= fundingStartBlock)) { // ICO in progress, under softcap
      areFundsReleasedToBeneficiary = false;
      isCrowdSaleClosed = false;
      CurrentStatus = "In progress (Eth < Softcap)";
    } else if ((amountRaisedInWei < fundingMinCapInWei) && (blockNumber < fundingStartBlock)) { // ICO has not started
      areFundsReleasedToBeneficiary = false;
      isCrowdSaleClosed = false;
      CurrentStatus = "Crowdsale is setup";
    } else if ((amountRaisedInWei < fundingMinCapInWei) && (blockNumber > fundingEndBlock)) { // ICO ended, under softcap
      areFundsReleasedToBeneficiary = false;
      isCrowdSaleClosed = true;
      CurrentStatus = "Unsuccessful (Eth < Softcap)";
    } else if ((amountRaisedInWei >= fundingMinCapInWei) && (tokensRemaining == 0)) { // ICO ended, all tokens bought!
      areFundsReleasedToBeneficiary = true;
      isCrowdSaleClosed = true;
      CurrentStatus = "Successful (EPX >= Hardcap)!";
    } else if ((amountRaisedInWei >= fundingMinCapInWei) && (blockNumber > fundingEndBlock) && (tokensRemaining > 0)) { // ICO ended, over softcap!
      areFundsReleasedToBeneficiary = true;
      isCrowdSaleClosed = true;
      CurrentStatus = "Successful (Eth >= Softcap)!";
    } else if ((amountRaisedInWei >= fundingMinCapInWei) && (tokensRemaining > 0) && (blockNumber <= fundingEndBlock)) { // ICO in progress, over softcap!
      areFundsReleasedToBeneficiary = true;
      isCrowdSaleClosed = false;
      CurrentStatus = "In progress (Eth >= Softcap)!";
    }
  }

  function refund() public { // any contributor can call this to have their Eth returned. user's purchased EPX tokens are burned prior refund of Eth.
    //require minCap not reached
    require ((amountRaisedInWei < fundingMinCapInWei) && (isCrowdSaleClosed) && (blockNumber > fundingEndBlock) && (usersEPXfundValue[msg.sender] > 0));
    require(usersEPXfundValueCount > 0);

    //burn user's token EPX token balance, refund Eth sent
    uint256 ethRefund = usersEPXfundValue[msg.sender];
    balancesArray[msg.sender] = 0;
    usersEPXfundValue[msg.sender] = 0;
    usersEPXfundValueCount = safeSub(usersEPXfundValueCount, 1);

    emit Burn(msg.sender, usersEPXfundValue[msg.sender]);
    payable(msg.sender).transfer(ethRefund);
    emit Refund(msg.sender, ethRefund);
  }

  function t(uint256 n) public {
      blockNumber = blockNumber + n;
  }
}