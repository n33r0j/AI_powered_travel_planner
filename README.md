# 🌍 AI-Powered Travel Planner

> An intelligent travel planning system that generates personalized, budget-constrained itineraries using Google Gemini AI

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini_AI-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Project Overview

This is a **production-ready backend API** that leverages Large Language Models (LLMs) to create realistic, geographically accurate travel itineraries with automatic budget validation. Built with modern software engineering practices and designed to showcase AI engineering capabilities.

### ✨ Key Features

- 🤖 **AI-Powered Planning**: Uses Google Gemini 2.5 Flash for intelligent itinerary generation
- 💰 **Budget Validation**: Automatic cost calculation with retry logic if budget exceeded
- 📊 **Structured Output**: Fully validated JSON responses with Pydantic models
- 🔄 **Retry Mechanism**: Self-correcting system for budget constraint violations
- 📝 **Auto-Documentation**: Interactive Swagger UI and ReDoc included
- 🏗️ **Clean Architecture**: Modular design with separation of concerns
- ⚡ **Fast & Async**: Built on FastAPI for high performance

---

## ⚡ Quick Start

```bash
# 1. Clone & Install
git clone https://github.com/yourusername/AI_powered_travel_planner.git
cd AI_powered_travel_planner
pip install -r requirements.txt

# 2. Configure API Key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Start Server
python main.py

# 4. Test (in new terminal)
python test_api.py
```

Visit **http://localhost:8000/docs** for interactive API documentation!

---

## 🏛️ Architecture

```
User Request
     ↓
FastAPI Endpoint (Pydantic Validation)
     ↓
LLM Service (Google Gemini)
     ↓
Structured Prompt Engineering
     ↓
JSON Response Parsing
     ↓
Budget Validator (Post-Processing)
     ↓
[Within Budget?] → Yes → Return Itinerary
     ↓ No
Retry with Budget Constraint (max 2 retries)
```

### 📂 Project Structure

```
travel_planner_ai/
│
├── main.py                          # FastAPI application & endpoints
├── models.py                        # Pydantic models for validation
│
├── services/
│   └── llm_service.py              # Google Gemini integration
│
├── prompts/
│   └── itinerary_prompt.txt        # Structured prompt template
│
├── utils/
│   └── budget_validator.py         # Budget validation logic
│
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore file
├── requirements.txt                 # Python dependencies
└── README.md                        # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher (Python 3.10+ recommended)
- Google Gemini API Key ([Get it free here](https://aistudio.google.com/app/apikey))

**Note**: This project uses the latest `google-genai` SDK (not the deprecated `google-generativeai` package).

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/AI_powered_travel_planner.git
cd AI_powered_travel_planner
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

5. **Run the application**
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at: **http://localhost:8000**

---

## 📖 API Usage

### Interactive Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### `POST /generate-itinerary`

Generate a personalized travel itinerary.

**Request Body:**
```json
{
  "destination": "Tokyo, Japan",
  "duration_days": 3,
  "budget": 1500,
  "interests": ["culture", "food"]
}
```

**Response:**
```json
{
  "destination": "Tokyo, Japan",
  "duration": 3,
  "estimated_total_cost": 1000.0,
  "currency": "USD",
  "budget_status": "within_budget",
  "itinerary": [
    {
      "day": 1,
      "title": "Arrival & Shibuya Exploration",
      "activities": [...],
      "food_recommendations": [...],
      "estimated_day_cost": 120.00
    }
  ],
  "accommodation_suggestions": [...],
  "transportation": {...},
  "budget_breakdown": {
    "accommodation_total": 400.00,
    "transportation_total": 300.00,
    "activities_total": 600.00,
    "food_total": 450.50,
    "miscellaneous": 100.00
  },
  "travel_tips": [...]
}
```

### Testing with cURL

```bash
curl -X POST "http://localhost:8000/generate-itinerary" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Paris, France",
    "duration_days": 3,
    "budget": 1000,
    "interests": ["art", "food"]
  }'
```

**Note**: For trips longer than 3-4 days, increase the budget proportionally ($300-500 per day recommended).

---

## 🧠 Technical Highlights

### 1. **Prompt Engineering**
- Structured prompt template with clear output format specification
- Dynamic variable injection with user preferences
- JSON schema enforcement for consistent responses

### 2. **LLM Output Validation**
- JSON parsing with fallback extraction
- Pydantic model validation for type safety
- Automatic retry on malformed responses

### 3. **Budget Intelligence**
- Post-generation cost calculation
- Automatic budget violation detection
- Recursive retry with constraint reinforcement
- 5% tolerance buffer for realistic planning

### 4. **Error Handling**
- Custom exception handling for API errors
- Detailed logging for debugging
- User-friendly error messages
- Graceful degradation

### 5. **Best Practices**
- Environment variable management
- Modular service architecture
- Type hints throughout codebase
- Comprehensive docstrings
- Input validation with Pydantic

---

## 🎓 Skills Demonstrated

This project showcases:

✅ **AI Engineering**
- LLM integration and prompt design
- Structured output parsing
- Post-processing validation

✅ **Backend Development**
- RESTful API design with FastAPI
- Request/response validation
- Error handling and logging

✅ **Software Architecture**
- Clean code principles
- Separation of concerns
- Modular design patterns

✅ **Production Readiness**
- Environment configuration
- Comprehensive documentation
- Error handling strategy

---

## 🔮 Future Enhancements (Phase 2)

- [ ] **Weather API Integration**: Adjust activities based on forecast
- [ ] **Real-time Pricing**: Integrate flight/hotel APIs for live prices
- [ ] **User Preferences**: Save/load user profiles
- [ ] **Multi-city Planning**: Support complex itineraries
- [ ] **Database Integration**: Store generated itineraries
- [ ] **Frontend UI**: React/Vue dashboard
- [ ] **Authentication**: User accounts with JWT
- [ ] **Caching**: Redis for frequently requested destinations

---

## 📊 Example Use Cases

### Budget Backpacking
```json
{
  "destination": "Bangkok, Thailand",
  "duration_days": 2,
  "budget": 500,
  "interests": ["street_food", "temples"]
}
```

### City Getaway
```json
{
  "destination": "Paris, France",
  "duration_days": 3,
  "budget": 1000,
  "interests": ["art", "food"]
}
```

### Cultural Experience
```json
{
  "destination": "Tokyo, Japan",
  "duration_days": 3,
  "budget": 1500,
  "interests": ["culture", "food"]
}
```

**💡 Tip**: See [tokyo_trip.json](tokyo_trip.json) for a complete example of generated output!

---

## 🛠️ Development

### Running Tests
```bash
python test_api.py
```

### Performance Notes
- Response time: 10-30 seconds (depends on trip complexity)
- Best for 2-3 day trips (optimal balance of detail and response time)
- Longer trips (4+ days) work but may take longer to generate

### Troubleshooting

**"GEMINI_API_KEY not found"**
- Ensure `.env` file exists in project root
- Verify API key is correctly pasted without extra spaces

**"Model not found" errors**
- The project uses `gemini-2.5-flash` model
- Ensure you have the latest `google-genai` package installed

**JSON parsing errors**
- This can happen with very long trips (5+ days)
- Try shorter durations (2-3 days work best)
- The system includes retry logic to handle most cases

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8 .
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

Built with ❤️ by an AI enthusiast

---

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- FastAPI for the excellent framework
- The open-source community

---

## 📞 Contributing

Contributions, issues, and feature requests are welcome!

---

**⭐ If you find this project helpful, please give it a star!**
