"""Currency conversion utilities for travel planner."""
from typing import Dict


class CurrencyConverter:
    """Simple currency converter with static exchange rates"""
    
    # Exchange rates (as of 2026, approximate)
    # Base: USD
    RATES = {
        "USD": 1.0,
        "INR": 83.0,  # 1 USD = 83 INR
    }
    
    def __init__(self):
        """Initialize currency converter"""
        pass
    
    def convert_to_usd(self, amount: float, from_currency: str) -> float:
        """
        Convert amount from specified currency to USD
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (USD, INR)
            
        Returns:
            Amount in USD
        """
        from_currency = from_currency.upper()
        
        if from_currency == "USD":
            return amount
        
        if from_currency not in self.RATES:
            raise ValueError(f"Unsupported currency: {from_currency}")
        
        # Convert to USD
        usd_amount = amount / self.RATES[from_currency]
        return round(usd_amount, 2)
    
    def convert_from_usd(self, amount: float, to_currency: str) -> float:
        """
        Convert amount from USD to specified currency
        
        Args:
            amount: Amount in USD
            to_currency: Target currency code (USD, INR)
            
        Returns:
            Amount in target currency
        """
        to_currency = to_currency.upper()
        
        if to_currency == "USD":
            return amount
        
        if to_currency not in self.RATES:
            raise ValueError(f"Unsupported currency: {to_currency}")
        
        # Convert from USD
        target_amount = amount * self.RATES[to_currency]
        return round(target_amount, 2)
    
    def get_currency_symbol(self, currency: str) -> str:
        """
        Get currency symbol for display
        
        Args:
            currency: Currency code
            
        Returns:
            Currency symbol
        """
        symbols = {
            "USD": "$",
            "INR": "₹",
        }
        return symbols.get(currency.upper(), currency)
    
    def get_rate_info(self, from_currency: str, to_currency: str) -> Dict[str, any]:
        """
        Get exchange rate information
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Dictionary with rate and formatted string
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return {"rate": 1.0, "formatted": f"1 {from_currency} = 1 {to_currency}"}
        
        # Calculate rate
        if from_currency == "USD":
            rate = self.RATES[to_currency]
        elif to_currency == "USD":
            rate = 1.0 / self.RATES[from_currency]
        else:
            # Convert through USD
            usd_rate = 1.0 / self.RATES[from_currency]
            rate = usd_rate * self.RATES[to_currency]
        
        return {
            "rate": round(rate, 2),
            "formatted": f"1 {from_currency} = {rate:.2f} {to_currency}"
        }


# Singleton instance
currency_converter = CurrencyConverter()
