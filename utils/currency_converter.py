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
    
    # Indian cities/regions for native currency detection
    INDIAN_DESTINATIONS = {
        # Major cities
        "delhi", "mumbai", "bangalore", "bengaluru", "kolkata", "chennai", "hyderabad",
        "pune", "ahmedabad", "jaipur", "surat", "lucknow", "kanpur", "nagpur",
        # Tourist destinations
        "goa", "kochi", "cochin", "kerala", "pondicherry", "puducherry", "agra", 
        "varanasi", "udaipur", "jaisalmer", "jodhpur", "shimla", "manali", "darjeeling",
        "rishikesh", "haridwar", "amritsar", "mysore", "ooty", "munnar", "alleppey",
        "hampi", "khajuraho", "ajanta", "ellora", "mahabalipuram", "madurai",
        # States
        "rajasthan", "maharashtra", "karnataka", "tamil nadu", "west bengal",
        "uttar pradesh", "gujarat", "andhra pradesh", "telangana", "punjab",
        "himachal pradesh", "uttarakhand", "jammu", "kashmir", "meghalaya",
        # Other
        "india", "andaman", "lakshadweep", "ladakh"
    }
    
    def __init__(self):
        """Initialize currency converter"""
        pass
    
    def is_indian_destination(self, destination: str) -> bool:
        """
        Check if destination is in India
        
        Args:
            destination: Destination name
            
        Returns:
            True if destination is in India
        """
        destination_lower = destination.lower().strip()
        return any(indian_dest in destination_lower for indian_dest in self.INDIAN_DESTINATIONS)
    
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
        Convert amount from USD to specified currency with smart rounding
        
        Args:
            amount: Amount in USD
            to_currency: Target currency code (USD, INR)
            
        Returns:
            Amount in target currency (intelligently rounded for realism)
        """
        to_currency = to_currency.upper()
        
        if to_currency == "USD":
            return amount
        
        if to_currency not in self.RATES:
            raise ValueError(f"Unsupported currency: {to_currency}")
        
        # Convert from USD
        target_amount = amount * self.RATES[to_currency]
        
        # Smart rounding for INR to avoid repetitive prices
        if to_currency == "INR":
            return self._round_inr_naturally(target_amount)
        
        return round(target_amount, 2)
    
    def _round_inr_naturally(self, amount: float) -> int:
        """
        Round INR amounts to natural numbers for realistic pricing
        
        Rules:
        - Under ₹50: Round to nearest ₹5 or ₹10
        - ₹50-200: Round to nearest ₹10 or ₹20
        - ₹200-500: Round to nearest ₹20 or ₹50
        - ₹500-1000: Round to nearest ₹50
        - Over ₹1000: Round to nearest ₹100
        
        Args:
            amount: Exact INR amount
            
        Returns:
            Naturally rounded INR amount
        """
        if amount < 50:
            # Round to nearest 10 for small amounts
            return max(10, round(amount / 10) * 10)
        elif amount < 200:
            # Round to nearest 20
            return round(amount / 20) * 20
        elif amount < 500:
            # Round to nearest 50
            return round(amount / 50) * 50
        elif amount < 1000:
            # Round to nearest 50 or 100
            rounded = round(amount / 50) * 50
            return rounded if rounded % 100 != 0 else rounded
        else:
            # Round to nearest 100
            return round(amount / 100) * 100
    
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
