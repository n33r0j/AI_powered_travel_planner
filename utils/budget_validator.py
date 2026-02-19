from typing import Dict, Any, Tuple


class BudgetValidator:
    """Validates and calculates budget for travel itineraries"""
    
    def __init__(self, tolerance_percentage: float = 5.0):
        """
        Initialize budget validator
        
        Args:
            tolerance_percentage: Allowed percentage over budget (default 5%)
        """
        self.tolerance_percentage = tolerance_percentage
    
    def validate_budget(
        self, 
        itinerary_data: Dict[str, Any], 
        user_budget: int
    ) -> Tuple[bool, float, Dict[str, float]]:
        """
        Validate if itinerary stays within budget
        
        Args:
            itinerary_data: Dictionary containing itinerary data
            user_budget: User's budget in USD
            
        Returns:
            Tuple of (is_valid, total_cost, breakdown)
            - is_valid: True if within budget (including tolerance)
            - total_cost: Calculated total cost
            - breakdown: Dictionary with cost breakdown by category
        """
        breakdown = self._calculate_breakdown(itinerary_data)
        total_cost = sum(breakdown.values())
        
        # Calculate maximum allowed budget (with tolerance)
        max_allowed = user_budget * (1 + self.tolerance_percentage / 100)
        
        is_valid = total_cost <= max_allowed
        
        return is_valid, total_cost, breakdown
    
    def _calculate_breakdown(self, itinerary_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate detailed cost breakdown from itinerary data
        
        Args:
            itinerary_data: Dictionary containing itinerary data
            
        Returns:
            Dictionary with breakdown by category
        """
        breakdown = {
            "accommodation_total": 0.0,
            "transportation_total": 0.0,
            "activities_total": 0.0,
            "food_total": 0.0,
            "miscellaneous": 0.0
        }
        
        # Use provided breakdown if available
        if "budget_breakdown" in itinerary_data:
            provided_breakdown = itinerary_data["budget_breakdown"]
            breakdown.update({
                "accommodation_total": float(provided_breakdown.get("accommodation_total", 0)),
                "transportation_total": float(provided_breakdown.get("transportation_total", 0)),
                "activities_total": float(provided_breakdown.get("activities_total", 0)),
                "food_total": float(provided_breakdown.get("food_total", 0)),
                "miscellaneous": float(provided_breakdown.get("miscellaneous", 0))
            })
        else:
            # Calculate from itinerary if breakdown not provided
            breakdown = self._calculate_from_itinerary(itinerary_data)
        
        return breakdown
    
    def _calculate_from_itinerary(self, itinerary_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate breakdown by parsing itinerary details
        
        Args:
            itinerary_data: Dictionary containing itinerary data
            
        Returns:
            Dictionary with calculated breakdown
        """
        breakdown = {
            "accommodation_total": 0.0,
            "transportation_total": 0.0,
            "activities_total": 0.0,
            "food_total": 0.0,
            "miscellaneous": 0.0
        }
        
        duration = itinerary_data.get("duration", 0)
        
        # Calculate activities and food costs from daily itinerary
        for day in itinerary_data.get("itinerary", []):
            # Activities
            for activity in day.get("activities", []):
                breakdown["activities_total"] += float(activity.get("estimated_cost", 0))
            
            # Food
            for food in day.get("food_recommendations", []):
                breakdown["food_total"] += float(food.get("estimated_cost", 0))
        
        # Calculate accommodation (average from suggestions)
        accommodations = itinerary_data.get("accommodation_suggestions", [])
        if accommodations:
            avg_per_night = sum(float(acc.get("price_per_night", 0)) for acc in accommodations) / len(accommodations)
            breakdown["accommodation_total"] = avg_per_night * duration
        
        # Calculate transportation
        transportation = itinerary_data.get("transportation", {})
        
        # To destination
        for transport in transportation.get("to_destination", []):
            breakdown["transportation_total"] += float(transport.get("estimated_cost", 0))
        
        # Local transport
        for transport in transportation.get("local_transport", []):
            daily_cost = float(transport.get("estimated_daily_cost", 0))
            breakdown["transportation_total"] += daily_cost * duration
        
        # Miscellaneous (10% of total for unexpected costs)
        subtotal = sum(breakdown.values())
        breakdown["miscellaneous"] = subtotal * 0.1
        
        return breakdown
    
    def get_budget_summary(
        self, 
        itinerary_data: Dict[str, Any], 
        user_budget: int
    ) -> Dict[str, Any]:
        """
        Get a comprehensive budget summary
        
        Args:
            itinerary_data: Dictionary containing itinerary data
            user_budget: User's budget in USD
            
        Returns:
            Dictionary with budget summary information
        """
        is_valid, total_cost, breakdown = self.validate_budget(itinerary_data, user_budget)
        
        remaining = user_budget - total_cost
        percentage_used = (total_cost / user_budget) * 100 if user_budget > 0 else 0
        
        return {
            "is_within_budget": is_valid,
            "user_budget": user_budget,
            "estimated_total_cost": total_cost,
            "remaining_budget": remaining,
            "percentage_used": round(percentage_used, 2),
            "breakdown": breakdown,
            "status": "within_budget" if is_valid else "over_budget"
        }
