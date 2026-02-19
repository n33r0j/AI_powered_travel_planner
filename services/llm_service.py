import os
import json
from google import genai
from google.genai import types
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

from models import TravelRequest, TravelResponse

# Load environment variables
load_dotenv()


class LLMService:
    """Service for interacting with Google Gemini LLM"""
    
    def __init__(self):
        """Initialize the Gemini API"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please create a .env file with your API key."
            )
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = 'gemini-2.5-flash'
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent / "prompts" / "itinerary_prompt.txt"
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()
    
    def generate_itinerary(self, request: TravelRequest, retry_count: int = 0) -> Dict[str, Any]:
        """
        Generate travel itinerary using Gemini LLM
        
        Args:
            request: TravelRequest object with user requirements
            retry_count: Number of retries attempted (for recursive budget adjustment)
            
        Returns:
            Dictionary containing the parsed itinerary
            
        Raises:
            ValueError: If JSON parsing fails
            Exception: If API call fails
        """
        try:
            # Format the prompt with user data
            formatted_prompt = self.prompt_template.format(
                destination=request.destination,
                duration=request.duration_days,
                budget=request.budget,
                interests=", ".join(request.interests)
            )
            
            # Add retry context if this is a budget adjustment
            if retry_count > 0:
                formatted_prompt += f"\n\nIMPORTANT: Previous attempt exceeded budget. Please ensure the total cost is BELOW ${request.budget}."
            
            # Build request with new API
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=formatted_prompt)]
                )
            ]
            
            # Configure generation settings
            config = types.GenerateContentConfig(
                temperature=0.5,
                top_p=0.95,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # Extract text from response - accumulate all parts
            response_text = ""
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                response_text += part.text
            
            # Fallback to simple text property
            if not response_text and hasattr(response, 'text'):
                response_text = response.text
            
            response_text = response_text.strip()
            
            if not response_text:
                raise ValueError("Empty response from API")
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON response
            try:
                itinerary_data = json.loads(response_text)
                return itinerary_data
            except json.JSONDecodeError as e:
                # Try to extract JSON from the response if it's embedded in text
                # Remove markdown code blocks
                cleaned_text = response_text
                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
                elif "```" in cleaned_text:
                    cleaned_text = cleaned_text.split("```")[1].split("```")[0]
                
                cleaned_text = cleaned_text.strip()
                
                # Try to find JSON object boundaries
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_str = cleaned_text[start_idx:end_idx + 1]
                    try:
                        itinerary_data = json.loads(json_str)
                        return itinerary_data
                    except json.JSONDecodeError:
                        pass
                
                # If all else fails, raise the original error with context
                raise ValueError(f"Failed to parse JSON response. Error: {str(e)}. Response preview: {response_text[:200]}")
        
        except Exception as e:
            raise Exception(f"Error generating itinerary: {str(e)}")
    
    def generate_with_budget_constraint(
        self, 
        request: TravelRequest, 
        max_retries: int = 2
    ) -> TravelResponse:
        """
        Generate itinerary with automatic budget validation and retry
        
        Args:
            request: TravelRequest object
            max_retries: Maximum number of retries if budget is exceeded
            
        Returns:
            TravelResponse object with validated itinerary
        """
        from utils.budget_validator import BudgetValidator
        
        validator = BudgetValidator()
        
        for attempt in range(max_retries + 1):
            # Generate itinerary
            itinerary_data = self.generate_itinerary(request, retry_count=attempt)
            
            # Validate budget
            is_valid, total_cost, breakdown = validator.validate_budget(
                itinerary_data, 
                request.budget
            )
            
            if is_valid:
                # Budget is within limits - success!
                travel_response = TravelResponse(**itinerary_data)
                travel_response.budget_status = "within_budget"
                return travel_response
            
            # If we've exhausted retries, return with over_budget status
            if attempt == max_retries:
                travel_response = TravelResponse(**itinerary_data)
                travel_response.budget_status = "over_budget"
                return travel_response
        
        # Should not reach here, but just in case
        raise Exception("Failed to generate valid itinerary")


# Singleton instance
llm_service = LLMService()
