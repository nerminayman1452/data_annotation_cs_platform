from decimal import Decimal, InvalidOperation

def safe_div(numerator, denominator):
    try:
        if not denominator or denominator == 0:
            return 0
        return float(numerator) / float(denominator)
    except (TypeError, ValueError, InvalidOperation):
        return 0