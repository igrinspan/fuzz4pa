pragma solidity >=0.4.25 <0.9.0;

library SafeMath {
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b);

        return c;
    }

    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b > 0);
        uint256 c = a / b;

        return c;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a);
        uint256 c = a - b;

        return c;
    }

    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a);

        return c;
    }

    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b != 0);
        return a % b;
    }
}

contract RefundEscrow {
    using SafeMath for uint256;

    enum State { Active, Refunding, Closed }

    event PrimaryTransferred(address recipient);
    event Deposited(address indexed payee, uint256 weiAmount);
    event Withdrawn(address indexed payee, uint256 weiAmount);
    event RefundsClosed();
    event RefundsEnabled();

    mapping(address => uint256) private _deposits;
    uint depositsCount = 0;
    State private _state;
    address payable private _beneficiary;
    address private _primary;

    constructor(address payable beneficiary) public {
        require(beneficiary != address(0));
        _beneficiary = beneficiary;
        _state = State.Active;
        _primary = msg.sender;
    }

    modifier onlyPrimary() {
        require(msg.sender == _primary);
        _;
    }

    function primary() public view returns (address) {
        return _primary;
    }

    function transferPrimary(address recipient) public onlyPrimary {
        require(recipient != address(0));
        _primary = recipient;
        emit PrimaryTransferred(_primary);
    }

    function depositsOf(address payee) internal view returns (uint256) {
        return _deposits[payee];
    }

    function withdrawalAllowed(address) internal view returns (bool) {
        return _state == State.Refunding;
    }

    function state() public view returns (State) {
        return _state;
    }

    function beneficiary() public view returns (address) {
        return _beneficiary;
    }

    function deposit(address refundee) public payable onlyPrimary {
        require(_state == State.Active);
        uint256 amount = msg.value;
        if (_deposits[refundee] == 0) {
            depositsCount += 1;
        }
        _deposits[refundee] = _deposits[refundee].add(amount);
        emit Deposited(refundee, amount);
    }

    function close() public onlyPrimary  {
        require(_state == State.Active);
        _state = State.Closed;
        emit RefundsClosed();
    }

    function enableRefunds() public onlyPrimary{
        require(_state == State.Active);
        _state = State.Refunding;
        emit RefundsEnabled();
    }

    function beneficiaryWithdraw() public {
        require(_state == State.Closed);
        require(address(this).balance > 0);
        _beneficiary.transfer(address(this).balance);
    }

    function withdraw(address payable payee) public {
        require(withdrawalAllowed(payee));
        require(depositsCount > 0);
        require(_deposits[payee] > 0);
        
        uint256 payment = _deposits[payee];
        _deposits[payee] = 0;
        payee.transfer(payment);
        depositsCount -= 1;
        emit Withdrawn(payee, payment);
    }
}