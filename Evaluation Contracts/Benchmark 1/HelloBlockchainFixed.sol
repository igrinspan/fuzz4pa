pragma solidity >=0.4.25 <0.9.0;

contract HelloBlockchain {
     //Set of States
    enum StateType { Request, Respond}

    //List of properties
    StateType State;
    address Requestor;
    address Responder;

    uint RequestMessageCode;
    uint ResponseMessageCode;

    // constructor function
    constructor(uint messageCode) public {
        Requestor = msg.sender;
        RequestMessageCode = messageCode;
        State = StateType.Request;
    }

    // call this function to send a request
    function SendRequest(uint requestMessageCode) public {
        require(Requestor == msg.sender);

        // FIX: Add precondition
        require(State == StateType.Respond);

        RequestMessageCode = requestMessageCode;
        State = StateType.Request;
    }

    // call this function to send a response
    function SendResponse(uint responseMessageCode) public {
        // FIX: Add precondition
        require(State == StateType.Request);

        Responder = msg.sender;

        // call ContractUpdated() to record this action
        ResponseMessageCode = responseMessageCode;
        State = StateType.Respond;
    }
}