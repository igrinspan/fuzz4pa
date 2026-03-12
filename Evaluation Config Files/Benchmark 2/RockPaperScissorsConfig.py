fileName = "RockPaperScissors.sol"
contractName = "RockPaperScissors"
functions = [
    "choicePlayer1(choice);",
    "choicePlayer2(choice);",
    "determineWinner();",
]
statePreconditions = [
    "p1Choice == -1",
    "p2Choice == -1",
    "p1Choice != -1 && p2Choice != -1",
]
functionPreconditions = [
    "msg.sender == player1 && (choice >= 0 && choice <= 2)",
    "msg.sender == player2 && (choice >= 0 && choice <= 2)",
    "true",
]
functionVariables = "int choice"

statesModeState = [[1,0,0,0,0,0], [0,2,0,0,0,0], [0,0,3,0,0,0], [0,0,0,4,0,0], [0,0,0,0,5,0], [0,0,0,0,0,6]]
statesNamesModeState = [
    "No bets", 
    "Only Player1 bets", 
    "Only Player2 bets", 
    "Both bet and Player1 wins", 
    "Both bet and Player2 wins", 
    "Both bet and Owner wins (draw)"
]
statePreconditionsModeState = [
    "p1Choice == -1 && p2Choice == -1", 
    "p1Choice != -1 && p2Choice == -1", 
    "p1Choice == -1 && p2Choice != -1", 
    "p1Choice != -1 && p2Choice != -1 && payoffMatrix[uint(p1Choice)][uint(p2Choice)] == 1",
    "p1Choice != -1 && p2Choice != -1 && payoffMatrix[uint(p1Choice)][uint(p2Choice)] == 2",
    "p1Choice != -1 && p2Choice != -1 && payoffMatrix[uint(p1Choice)][uint(p2Choice)] == 0",
]

