from dataclasses import dataclass

@dataclass
class EchidnaConfigData:
    """ Config File data that Echidna uses to execute. 
    I initialize it with default parameters (except testMode and shrinkLimit). """
    testLimit: int = 50000
    balanceContract: int = 0
    workers: int = 1
    maxValue: int = 100000000000000000000
    testMode: str = "assertion"
    format: str = "Null"
    shrinkLimit: int = 0
    seqLen: int = 100 

