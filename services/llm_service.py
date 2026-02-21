import os
import json
import re
import logging
from google import genai
from google.genai import types
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

from models import TravelRequest, TravelResponse

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


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
    
    def _fix_json_string(self, json_str: str) -> str:
        """
        Attempt to fix common JSON syntax errors
        
        Args:
            json_str: Potentially malformed JSON string
            
        Returns:
            Fixed JSON string
        """
        # Remove any text before first { and after last }
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            return json_str
        
        json_str = json_str[start_idx:end_idx + 1]
        
        # Fix common issues
        # 1. Remove trailing commas before ] or }
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 2. Add missing commas between objects (basic heuristic)
        # This is risky, so we'll be conservative
        json_str = re.sub(r'}\s*{', '},{', json_str)
        json_str = re.sub(r']\s*\[', '],[', json_str)
        
        # 3. Fix unescaped quotes in strings (very basic)
        # This is complex, so we'll skip for now
        
        return json_str
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Robustly parse JSON from LLM response
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Step 1: Clean up markdown formatting
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # Step 2: Try direct parsing first
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {str(e)}")
        
        # Step 3: Extract JSON boundaries
        start_idx = cleaned_text.find('{')
        end_idx = cleaned_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned_text[start_idx:end_idx + 1]
            
            # Try parsing extracted JSON
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Extracted JSON parse failed: {str(e)}")
                
                # Step 4: Try fixing common issues
                fixed_json = self._fix_json_string(json_str)
                try:
                    return json.loads(fixed_json)
                except json.JSONDecodeError as e2:
                    logger.error(f"Fixed JSON parse failed: {str(e2)}")
                    # Save problematic response for debugging
                    debug_file = Path(__file__).parent.parent / f"debug_response_{hash(response_text)}.txt"
                    with open(debug_file, 'w') as f:
                        f.write(f"Original:\n{response_text}\n\n")
                        f.write(f"Cleaned:\n{cleaned_text}\n\n")
                        f.write(f"Extracted:\n{json_str}\n\n")
                        f.write(f"Fixed:\n{fixed_json}\n\n")
                        f.write(f"Error: {str(e2)}")
                    logger.error(f"Debug response saved to: {debug_file}")
                    
                    raise ValueError(
                        f"Failed to parse JSON response after multiple attempts. "
                        f"Error: {str(e2)}. "
                        f"Debug file saved. "
                        f"Response preview: {response_text[:300]}"
                    )
        
        raise ValueError(f"Could not find JSON object in response. Preview: {response_text[:300]}")
    
    def generate_itinerary(
        self, 
        request: TravelRequest, 
        retry_count: int = 0,
        weather_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate travel itinerary using Gemini LLM
        
        Args:
            request: TravelRequest object with user requirements
            retry_count: Number of retries attempted (for recursive budget adjustment)
            weather_context: Optional weather forecast context
            
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
                interests=", ".join(request.interests),
                weather_context=weather_context if weather_context else ""
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
            # Increased max_output_tokens for longer itineraries with premium content
            config = types.GenerateContentConfig(
                temperature=0.5,
                top_p=0.95,
                max_output_tokens=16384,  # Doubled to handle detailed itineraries
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
            
            # Check if response appears truncated (incomplete JSON)
            if not response_text.endswith('}'):
                logger.warning(
                    f"Response appears truncated (length: {len(response_text)}). "
                    f"Last 100 chars: ...{response_text[-100:]}"
                )
                # If this is not a retry, throw error to trigger retry
                if retry_count == 0:
                    raise ValueError(
                        "Response appears truncated (does not end with closing brace). "
                        "This will be retried with adjusted parameters."
                    )
            
            # Parse JSON response using robust parser
            itinerary_data = self._parse_json_response(response_text)
            return itinerary_data
        
        except Exception as e:
            raise Exception(f"Error generating itinerary: {str(e)}")
    
    def generate_with_budget_constraint(
        self, 
        request: TravelRequest, 
        max_retries: int = 2,
        weather_context: str = ""
    ) -> TravelResponse:
        """
        Generate itinerary with automatic budget validation and retry
        
        Args:
            request: TravelRequest object
            max_retries: Maximum number of retries if budget is exceeded OR underutilized
            weather_context: Optional weather forecast context
            
        Returns:
            TravelResponse object with validated itinerary
        """
        from utils.budget_validator import BudgetValidator
        
        validator = BudgetValidator()
        last_error = None
        budget_utilization_retry_used = False
        
        for attempt in range(max_retries + 1):
            try:
                # Generate itinerary
                itinerary_data = self.generate_itinerary(
                    request, 
                    retry_count=attempt,
                    weather_context=weather_context
                )
                
                # Validate budget
                is_valid, total_cost, breakdown = validator.validate_budget(
                    itinerary_data, 
                    request.budget
                )
                
                # Calculate budget utilization
                utilization_percentage = (total_cost / request.budget) * 100
                
                logger.info(f"Budget utilization: {utilization_percentage:.1f}% (${total_cost:.2f} of ${request.budget})")
                
                # Check if budget is significantly underutilized (< 75%)
                if utilization_percentage < 75 and not budget_utilization_retry_used and attempt < max_retries:
                    logger.warning(
                        f"Budget underutilized: {utilization_percentage:.1f}%. "
                        f"Retrying with instructions to increase quality..."
                    )
                    budget_utilization_retry_used = True
                    
                    # Add special instruction for next attempt
                    original_prompt = self.prompt_template
                    self.prompt_template = original_prompt + f"""

**IMPORTANT BUDGET UTILIZATION INSTRUCTION:**
Your previous response only used ${total_cost:.2f} ({utilization_percentage:.1f}%) of the ${request.budget} budget.
This is TOO LOW and provides poor value.

Please regenerate with:
- Higher quality accommodations (aim for ${request.budget * 0.4:.0f} for lodging)
- More premium activities and experiences (aim for ${request.budget * 0.25:.0f})
- Better dining options (aim for ${request.budget * 0.2:.0f})
- Comfortable transportation (aim for ${request.budget * 0.12:.0f})

TARGET: Use 85-95% of the ${request.budget} budget for an optimized experience.
Keep responses concise to avoid truncation.
"""
                    try:
                        # Retry with enhanced prompt
                        itinerary_data = self.generate_itinerary(
                            request, 
                            retry_count=0,  # Reset retry count for fresh attempt
                            weather_context=weather_context
                        )
                        # Validate new response
                        is_valid, total_cost, breakdown = validator.validate_budget(
                            itinerary_data, 
                            request.budget
                        )
                        new_utilization = (total_cost / request.budget) * 100
                        logger.info(f"After optimization: {new_utilization:.1f}% utilization")
                    except Exception as opt_error:
                        logger.error(f"Budget optimization retry failed: {str(opt_error)}")
                        # Continue with original response if optimization fails
                        logger.info("Falling back to original response")
                    finally:
                        # Restore original prompt
                        self.prompt_template = original_prompt
                
                # Check if within acceptable range (don't exceed with tolerance)
                if is_valid:
                    travel_response = TravelResponse(**itinerary_data)
                    travel_response.budget_status = "within_budget"
                    
                    # Log final utilization
                    final_utilization = (total_cost / request.budget) * 100
                    if final_utilization < 75:
                        logger.warning(f"Final budget utilization is low: {final_utilization:.1f}%")
                    elif final_utilization >= 85:
                        logger.info(f"Optimal budget utilization achieved: {final_utilization:.1f}%")
                    
                    return travel_response
                
                # If we've exhausted retries, return with over_budget status
                if attempt == max_retries:
                    travel_response = TravelResponse(**itinerary_data)
                    travel_response.budget_status = "over_budget"
                    logger.warning(f"Budget exceeded: ${total_cost:.2f} > ${request.budget}")
                    return travel_response
                    
            except ValueError as e:
                # JSON parsing error - retry
                logger.warning(f"Attempt {attempt + 1} failed with ValueError: {str(e)}")
                last_error = e
                if "JSON" in str(e) or "parse" in str(e).lower():
                    if attempt < max_retries:
                        logger.info(f"Retrying due to JSON parsing error (attempt {attempt + 1}/{max_retries + 1})")
                        continue
                raise
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                last_error = e
                if attempt < max_retries:
                    continue
                raise
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise Exception("Failed to generate valid itinerary")


# Singleton instance
llm_service = LLMService()
