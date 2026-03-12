pragma solidity >=0.4.25 <0.9.0;

contract AssetTransfer {
    
    enum StateType { Active, OfferPlaced, PendingInspection, Inspected, Appraised, NotionalAcceptance, BuyerAccepted, SellerAccepted, Accepted, Terminated }
    address InstanceOwner;
    uint AskingPrice;
    StateType State;

    address InstanceBuyer;
    uint OfferPrice;
    address InstanceInspector;
    address InstanceAppraiser;

    constructor(uint256 price) public {
        InstanceOwner = msg.sender;
        AskingPrice = price;
        State = StateType.Active;
    }

    function Terminate() public {
        require(InstanceOwner == msg.sender);

        // FIX: Add this precondition
        require(State != StateType.Terminated && State != StateType.Accepted && State != StateType.SellerAccepted);

        State = StateType.Terminated;
    }

    function Modify(uint256 price) public {
        require(State == StateType.Active);
        require(InstanceOwner == msg.sender);

        AskingPrice = price;
    }

    function MakeOffer(address inspector, address appraiser, uint256 offerPrice) public {
        require(inspector != address(0) && appraiser != address(0) && offerPrice != 0);
        require(State == StateType.Active);
        // Cannot enforce "AllowedRoles":["Buyer"] because Role information is unavailable
        require(InstanceOwner != msg.sender); // not expressible in the current specification language

        InstanceBuyer = msg.sender;
        InstanceInspector = inspector;
        InstanceAppraiser = appraiser;
        OfferPrice = offerPrice;
        State = StateType.OfferPlaced;
    }

    function AcceptOffer() public {
        require(State == StateType.OfferPlaced);
        require(InstanceOwner == msg.sender);
        State = StateType.PendingInspection;
    }

    function Reject() public {
        require(State == StateType.OfferPlaced || State == StateType.PendingInspection || State == StateType.Inspected || State == StateType.Appraised || State == StateType.NotionalAcceptance || State == StateType.BuyerAccepted);
        require(InstanceOwner == msg.sender);

        InstanceBuyer = address(0);
        State = StateType.Active;
    }

    function Accept() public {
        require(msg.sender == InstanceBuyer || msg.sender == InstanceOwner);

        require(!(msg.sender == InstanceOwner &&
            State != StateType.NotionalAcceptance &&
            State != StateType.BuyerAccepted));

        require(!(msg.sender == InstanceBuyer &&
            State != StateType.NotionalAcceptance &&
            State != StateType.SellerAccepted));

        if (msg.sender == InstanceBuyer) {
            if (State == StateType.NotionalAcceptance) {
                State = StateType.BuyerAccepted;
            }
            else if (State == StateType.SellerAccepted) {
                State = StateType.Accepted;
            }
        }
        else {
            if (State == StateType.NotionalAcceptance) {
                State = StateType.SellerAccepted;
            }
            else if (State == StateType.BuyerAccepted) {
                State = StateType.Accepted;
            }
        }
    }

    function ModifyOffer(uint256 offerPrice) public {
        require(State == StateType.OfferPlaced);
        require(InstanceBuyer == msg.sender && offerPrice != 0);
        OfferPrice = offerPrice;
    }

    function RescindOffer() public {
        require(State == StateType.OfferPlaced || State == StateType.PendingInspection || State == StateType.Inspected || State == StateType.Appraised || State == StateType.NotionalAcceptance || State == StateType.SellerAccepted);
        require(InstanceBuyer == msg.sender);

        InstanceBuyer = address(0);
        OfferPrice = 0;
        State = StateType.Active;
    }

    function MarkAppraised() public {
        require(InstanceAppraiser == msg.sender);

        require(State == StateType.PendingInspection || State == StateType.Inspected);

        if (State == StateType.PendingInspection) {
            State = StateType.Appraised;
        }
        else if (State == StateType.Inspected) {
            State = StateType.NotionalAcceptance;
        }
    }

    function MarkInspected() public {
        require(InstanceInspector == msg.sender);

        require(State == StateType.PendingInspection || State == StateType.Appraised);

        if (State == StateType.PendingInspection) {
            State = StateType.Inspected;
        }
        else if (State == StateType.Appraised) {
            State = StateType.NotionalAcceptance;
        }
    }
}
