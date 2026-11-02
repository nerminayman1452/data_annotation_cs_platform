from decimal import Decimal


class Config:
    
    #fee for +1000 units
    PLATFORM_FEE_PERCENTAGE = Decimal("20.0")
    QUESTION_BANK_FEE = Decimal("5.0")
    MAX_UNIT = 1000