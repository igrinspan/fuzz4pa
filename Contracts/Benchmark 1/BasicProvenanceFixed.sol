pragma solidity >=0.4.25 <0.9.0;

contract BasicProvenance {

    //Set of States
    enum StateType { Created, InTransit, Completed}
    
    //List of properties
    StateType State;
    address InitiatingCounterparty;
    address Counterparty;
    address PreviousCounterparty;
    address SupplyChainOwner;
    address SupplyChainObserver;
    
    constructor(address supplyChainOwner, address supplyChainObserver) public {
        InitiatingCounterparty = msg.sender;
        Counterparty = InitiatingCounterparty;
        SupplyChainOwner = supplyChainOwner;
        SupplyChainObserver = supplyChainObserver;
        State = StateType.Created;
    }

    function TransferResponsibility(address newCounterparty) public {

        require(Counterparty == msg.sender && State != StateType.Completed);

        if (State == StateType.Created) {
            State = StateType.InTransit;
        }

        PreviousCounterparty = Counterparty;
        Counterparty = newCounterparty;
    }

    function Complete() public {
        require(SupplyChainOwner == msg.sender && State != StateType.Completed);

        //FIX: Add precondition
        require(State != StateType.Created);

        State = StateType.Completed;
        PreviousCounterparty = Counterparty;
        Counterparty = address(0);
    }
}
