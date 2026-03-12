pragma solidity >=0.4.25 <0.9.0;

contract SimpleMarketplace {
    enum StateType { 
      ItemAvailable,
      OfferPlaced,
      Accepted
    }

    address InstanceOwner;
    int AskingPrice;
    StateType State;

    address InstanceBuyer;
    int OfferPrice;

    constructor(int price) public {
        InstanceOwner = msg.sender;
        AskingPrice = price;
        State = StateType.ItemAvailable;
    }

    function MakeOffer(int offerPrice) public {
        require(offerPrice != 0);
        require(State == StateType.ItemAvailable);
        require(InstanceOwner != msg.sender);

        InstanceBuyer = msg.sender;
        OfferPrice = offerPrice;
        State = StateType.OfferPlaced;
    }

    function Reject() public {
        require(State == StateType.OfferPlaced);
        require(InstanceOwner == msg.sender);

        InstanceBuyer = address(0);
        State = StateType.ItemAvailable;
    }

    function AcceptOffer() public {
        require(msg.sender == InstanceOwner);

        //FIX: Add precondition
        require(State != StateType.ItemAvailable && State != StateType.Accepted);

        State = StateType.Accepted;
    }
}