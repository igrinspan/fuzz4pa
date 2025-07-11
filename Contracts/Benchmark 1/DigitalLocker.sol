pragma solidity >=0.4.25 <0.9.0;

contract DigitalLocker {
    enum StateType { Requested, DocumentReview, AvailableToShare, SharingRequestPending, SharingWithThirdParty, Terminated }
    address public Owner;
    address public BankAgent;
    string public LockerFriendlyName;
    string public LockerIdentifier;
    address public CurrentAuthorizedUser;
    string public ExpirationDate;
    string public Image;
    address public ThirdPartyRequestor;
    string public IntendedPurpose;
    string public LockerStatus;
    string public RejectionReason;
    StateType public State;

    constructor(string memory lockerFriendlyName, address bankAgent) public {
        Owner = msg.sender;
        LockerFriendlyName = lockerFriendlyName;
        State = StateType.DocumentReview; // should be StateType.Requested?
        BankAgent = bankAgent;
    }

    function BeginReviewProcess() public {
        /* Need to update, likely with registry to confirm sender is agent
        Also need to add a function to re-assign the agent.
        */
        require(Owner != msg.sender);

        BankAgent = msg.sender;
        LockerStatus = "Pending";
        State = StateType.DocumentReview;
    }

    function RejectApplication(string memory rejectionReason) public {
        require(BankAgent == msg.sender);

        RejectionReason = rejectionReason;
        LockerStatus = "Rejected";
        State = StateType.DocumentReview;
    }

    function UploadDocuments(string memory lockerIdentifier, string memory image) public {
        require(BankAgent == msg.sender);
        LockerStatus = "Approved";
        Image = image;
        LockerIdentifier = lockerIdentifier;
        State = StateType.AvailableToShare;
    }

    function ShareWithThirdParty(address thirdPartyRequestor, string memory expirationDate, string memory intendedPurpose) public {
        require(Owner == msg.sender);

        ThirdPartyRequestor = thirdPartyRequestor;
        CurrentAuthorizedUser = ThirdPartyRequestor;
        LockerStatus = "Shared";
        IntendedPurpose = intendedPurpose;
        ExpirationDate = expirationDate;
        State = StateType.SharingWithThirdParty;
    }

    function AcceptSharingRequest() public {
        require(Owner == msg.sender);

        CurrentAuthorizedUser = ThirdPartyRequestor;
        State = StateType.SharingWithThirdParty;
    }

    function RejectSharingRequest() public {
        require(Owner == msg.sender);
        LockerStatus = "Available";
        CurrentAuthorizedUser = 0x0000000000000000000000000000000000000000;
        State = StateType.AvailableToShare;
    }

    function RequestLockerAccess(string memory intendedPurpose) public {
        require(Owner != msg.sender);

        ThirdPartyRequestor = msg.sender;
        IntendedPurpose = intendedPurpose;
        State = StateType.SharingRequestPending;
    }

    function ReleaseLockerAccess() public {
        require(CurrentAuthorizedUser == msg.sender);
        LockerStatus = "Available";
        ThirdPartyRequestor = 0x0000000000000000000000000000000000000000;
        CurrentAuthorizedUser = 0x0000000000000000000000000000000000000000;
        IntendedPurpose = "";
        State = StateType.AvailableToShare;
    }
    
    function RevokeAccessFromThirdParty() public {
        require(Owner == msg.sender);
        LockerStatus = "Available";
        CurrentAuthorizedUser = 0x0000000000000000000000000000000000000000;
        State = StateType.AvailableToShare;
    }

    function Terminate() public {
        require(Owner == msg.sender);
        CurrentAuthorizedUser = 0x0000000000000000000000000000000000000000;
        State = StateType.Terminated;
    }
}
