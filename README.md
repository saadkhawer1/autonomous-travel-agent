# 🌍 Autonomous Travel Planning Agent

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-green)
![LangChain](https://img.shields.io/badge/LangChain-Framework-success)
![Gemini](https://img.shields.io/badge/Google-Gemini-orange)
![License](https://img.shields.io/badge/License-MIT-red)

</p>

> **An AI-powered autonomous travel planning agent that researches destinations, estimates travel costs, checks weather, recommends hotels and attractions, optimizes travel routes, and generates complete multi-day itineraries using LangGraph and Google Gemini.**

---

# 📖 Overview

Planning a trip usually requires visiting multiple websites to compare hotels, attractions, weather forecasts, travel routes, and estimated costs.

This project automates the complete planning process using an autonomous AI agent.

The agent gathers information from multiple APIs, reasons over the collected data, validates its own output using a Critic/Reflection node, and finally generates a complete travel itinerary with budget estimation and explanations.

---

# 🎯 Objectives

- Generate complete travel itineraries
- Stay within the user's budget
- Search attractions automatically
- Recommend hotels & restaurants
- Check weather conditions
- Estimate transportation cost
- Calculate travel routes
- Recover from API failures
- Improve response quality using Reflection

---

# ✨ Features

- 🤖 Autonomous AI Agent
- 🧠 LangGraph Workflow
- 💬 Google Gemini LLM
- 🌍 Multi-Day Trip Planning
- 💰 Budget Optimization
- 🏨 Hotel Recommendations
- 🍽️ Restaurant Recommendations
- 📍 Attraction Discovery
- 🌦️ Live Weather
- 🚗 Route Optimization
- 🗺️ Distance Calculation
- 🔍 Real-time Web Search
- 📊 Budget Breakdown
- 🔄 Reflection / Critic Node
- ⚠️ Graceful Error Handling

---

# 🏗️ System Architecture

```text
                 User

                   │

                   ▼

            User Request

                   │

                   ▼

        Planner / Coordinator

                   │

      ┌────────────┼────────────┐

      ▼            ▼            ▼

 Web Search     Places API   Weather API

   Tavily        Geoapify   OpenWeather

      │            │            │

      └────────────┼────────────┘

                   ▼

          Route Optimization

         OpenRouteService

                   │

                   ▼

          Budget Estimation

                   │

                   ▼

      Reflection / Critic Node

        ✔ Budget Check

        ✔ API Validation

        ✔ Missing Data Check

                   │

                   ▼

       Final Travel Itinerary
```

---

# 🧠 Agent Workflow

### Step 1

User enters

- Destination
- Budget
- Duration

Example

```
Plan a 5-day trip to Hunza under PKR 120,000.
```

---

### Step 2

The agent searches

- Attractions
- Hotels
- Restaurants
- Weather
- Routes
- Transportation

---

### Step 3

Cost estimation

- Hotel
- Food
- Activities
- Transportation
- Miscellaneous

---

### Step 4

Reflection

The Critic Node checks

- Budget
- Missing Information
- API Errors
- Weather
- Route Quality

---

### Step 5

Final Output

- Day-wise itinerary
- Hotel recommendation
- Restaurant recommendation
- Weather summary
- Route information
- Budget breakdown
- Planning justification

---

# 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Programming Language |
| Google Gemini | LLM |
| LangGraph | Agent Workflow |
| LangChain | Tool Integration |
| Tavily | Web Search |
| Geoapify | Places Search |
| OpenWeatherMap | Weather |
| OpenRouteService | Routing |
| dotenv | Environment Variables |
| Requests | API Calls |

---

# 🔑 APIs Used

| API | Purpose |
|------|---------|
| Google Gemini API | AI reasoning and itinerary generation |
| Tavily Search API | Web search |
| Geoapify API | Hotels, restaurants, attractions |
| OpenWeatherMap API | Weather forecast |
| OpenRouteService API | Route planning |

---

# 📊 API Research

## Web Search APIs

| API | Status |
|------|--------|
| ✅ Tavily | Selected |
| DuckDuckGo | Rejected |
| Serper.dev | Rejected |

---

## Places APIs

| API | Status |
|------|--------|
| ✅ Geoapify | Selected |
| OpenStreetMap | Rejected |
| Google Places | Rejected |

---

## Weather APIs

| API | Status |
|------|--------|
| ✅ OpenWeatherMap | Selected |
| WeatherAPI | Rejected |
| Open-Meteo | Rejected |

---

## Routing APIs

| API | Status |
|------|--------|
| ✅ OpenRouteService | Selected |
| Google Directions | Rejected |
| Mapbox | Rejected |

---

# 📂 Project Structure

```text
travel-agent/

│

├── main.py

├── graph.py

├── state.py

├── planner.py

├── prompts.py

├── tools.py

├── requirements.txt

├── README.md

├── .env

│

└── utils/

    ├── search.py

    ├── routing.py

    ├── weather.py

    └── budget.py
```

---

# ⚙️ Installation

Clone repository

```bash
git clone https://github.com/yourusername/autonomous-travel-agent.git
```

Move into project

```bash
cd autonomous-travel-agent
```

(Optional) Create Virtual Environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file

```env
GEMINI_API_KEY=

TAVILY_API_KEY=

GEOAPIFY_API_KEY=

OPENWEATHERMAP_API_KEY=

OPENROUTESERVICE_API_KEY=
```

---

# ▶️ Run the Project

```bash
python main.py
```

---

# 💻 Example Usage

```
Destination: Hunza

Budget: PKR 120000

Duration: 5 Days
```

or

```
Plan a 5-day trip to Hunza under PKR 120000.
```

---

# 📌 Sample Output

```
Destination:
Hunza

Weather:
18°C

Hotel:
Mountain Lodge

Restaurants:
Cafe De Hunza

Budget:
PKR 118000

Activities:
Altit Fort
Baltit Fort
Attabad Lake

Transportation:
Private Car

Status:
Within Budget
```

---

# 🛡️ Error Handling

The system automatically handles

- Invalid destination
- Missing weather
- Empty search results
- Route failures
- API timeout
- Budget overflow
- Network issues

---

# 🚀 Future Improvements

## AI

- Multi-Agent System
- User Memory
- Personalized Recommendations
- Dynamic Planning

## Travel

- Flight Booking
- Hotel Booking
- Visa Information
- Currency Conversion
- Event Discovery

## User Experience

- Interactive Maps
- PDF Export
- Email Itinerary
- WhatsApp Bot
- Telegram Bot
- Voice Assistant
- Mobile App

## Advanced AI

- ML Budget Prediction
- Crowd Density Prediction
- Traffic Analysis
- Eco-friendly Recommendations

---

# 📚 Learning Outcomes

This project demonstrates

- Autonomous AI Agents
- LangGraph
- LangChain
- Tool Calling
- Prompt Engineering
- State Management
- API Integration
- Reflection Pattern
- Budget Optimization
- Error Recovery

---

# 🤝 Contributing

Contributions are welcome.

1. Fork this repository.
2. Create a feature branch.
3. Commit your changes.
4. Push your branch.
5. Open a Pull Request.

---

# 📄 License

This project was developed as part of the **AI Summer Internship 2026** for educational and learning purposes.

---

⭐ If you found this project helpful, consider giving it a **Star** on GitHub!
