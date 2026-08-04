import os
import requests
from langchain_core.tools import tool

def _get_env_key(key_name: str) -> str:
    key = os.environ.get(key_name)
    if not key:
        raise ValueError(f"Missing environment variable: {key_name}")
    return key

@tool
def search_tool(query: str) -> str:
    """
    Search Tool: Queries the Tavily API for general destination info, tourist attractions, etc.
    Returns a summary of the search results.
    """
    try:
        api_key = _get_env_key("TAVILY_API_KEY")
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "include_answer": True
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        answer = data.get("answer", "")
        results = data.get("results", [])
        
        summary = f"Answer: {answer}\n\nTop Results:\n"
        for r in results[:3]:
            summary += f"- {r.get('title')}: {r.get('content')}\n"
        return summary
    except Exception as e:
        return f"Search tool failed: {str(e)}"

def _get_coordinates(destination: str, api_key: str = None):
    """Helper to get coordinates for a destination using Nominatim."""
    url = f"https://nominatim.openstreetmap.org/search?q={destination}&format=json&limit=1"
    headers = {"User-Agent": "TravelAgentBot/1.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError(f"Could not find coordinates for {destination}")
    lon = data[0]["lon"]
    lat = data[0]["lat"]
    return lat, lon

@tool
def places_tool(destination: str, category: str) -> str:
    """
    Places Tool: Searches for attractions, restaurants, museums, or hotels using Nominatim (OpenStreetMap).
    Valid categories: 'tourism', 'restaurant', 'hotel', 'landmark', etc.
    Returns names, types, and coordinates.
    """
    try:
        query = f"{category} in {destination}"
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=5"
        headers = {"User-Agent": "TravelAgentBot/1.0"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return f"No places found for category '{category}' in {destination}."
            
        places = []
        for item in data:
            name = item.get("name", "Unnamed")
            if not name:
                name = item.get("display_name", "Unnamed").split(",")[0]
            place_type = item.get("type", "unknown")
            lon = item.get("lon")
            lat = item.get("lat")
            places.append(f"Name: {name}, Type: {place_type}, Coords: ({lat}, {lon})")
            
        return "\n".join(places)
    except Exception as e:
        return f"Places tool failed: {str(e)}"

@tool
def weather_tool(destination: str) -> str:
    """
    Weather Tool: Retrieves the forecast, temperature range, and conditions for the destination using OpenWeatherMap.
    Since we plan for general trip dates, this gets the upcoming 5-day forecast to approximate conditions.
    """
    try:
        api_key = _get_env_key("OPENWEATHERMAP_API_KEY")
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={destination}&appid={api_key}&units=metric"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        list_data = data.get("list", [])
        if not list_data:
            return f"No forecast data available for {destination}."
            
        # Extract a summary of the next 5 days
        summary_days = {}
        for item in list_data:
            date_txt = item.get("dt_txt", "").split(" ")[0]
            temp = item.get("main", {}).get("temp")
            desc = item.get("weather", [{}])[0].get("description")
            pop = item.get("pop", 0) # Probability of precipitation
            
            if date_txt not in summary_days:
                summary_days[date_txt] = {"temps": [], "desc": set(), "pop": []}
                
            summary_days[date_txt]["temps"].append(temp)
            summary_days[date_txt]["desc"].add(desc)
            summary_days[date_txt]["pop"].append(pop)
            
        result = f"5-Day Weather Summary for {destination}:\n"
        for date, info in list(summary_days.items())[:5]:
            min_temp = min(info["temps"])
            max_temp = max(info["temps"])
            max_pop = max(info["pop"]) * 100
            desc = ", ".join(info["desc"])
            result += f"- {date}: Temp {min_temp:.1f}C to {max_temp:.1f}C. Rain prob: {max_pop:.0f}%. Conditions: {desc}\n"
            
        return result
    except Exception as e:
        return f"Weather tool failed: {str(e)}"

@tool
def routing_tool(start_lat: str, start_lon: str, end_lat: str, end_lon: str, profile: str = "driving-car") -> str:
    """
    Routing Tool: Returns travel time and distance between two coordinates.
    `profile` can be 'driving-car' or 'foot-walking'.
    """
    try:
        api_key = _get_env_key("OPENROUTESERVICE_API_KEY")
        
        # Cast to float internally to handle Groq string-passing quirks
        slat = float(start_lat)
        slon = float(start_lon)
        elat = float(end_lat)
        elon = float(end_lon)
        
        url = f"https://api.openrouteservice.org/v2/directions/{profile}?api_key={api_key}&start={slon},{slat}&end={elon},{elat}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
             return f"Routing tool failed: {response.text}"
             
        data = response.json()
        features = data.get("features", [])
        if not features:
            return "No route found."
            
        summary = features[0].get("properties", {}).get("summary", {})
        distance_km = summary.get("distance", 0) / 1000.0
        duration_mins = summary.get("duration", 0) / 60.0
        
        return f"Distance: {distance_km:.2f} km. Estimated travel time: {duration_mins:.1f} minutes via {profile}."
    except Exception as e:
        return f"Routing tool failed: {str(e)}"

@tool
def cost_estimator(hotel_cost: str, transport_cost: str, meals_cost: str, activities_cost: str, budget: str) -> str:
    """
    Cost Estimator: Calculates total cost from components and compares against the budget.
    Returns a string detailing the breakdown and whether it is under or over budget.
    (No API - pure calculation logic).
    """
    try:
        h_cost = float(hotel_cost)
        t_cost = float(transport_cost)
        m_cost = float(meals_cost)
        a_cost = float(activities_cost)
        b = float(budget)
        
        total_cost = h_cost + t_cost + m_cost + a_cost
        difference = b - total_cost
    
        result = (
            f"Cost Breakdown:\n"
            f"- Hotel: {h_cost}\n"
            f"- Transport: {t_cost}\n"
            f"- Meals: {m_cost}\n"
            f"- Activities: {a_cost}\n"
            f"-------------------\n"
            f"Total Cost: {total_cost}\n"
            f"Budget: {b}\n"
        )
        
        if difference >= 0:
            result += f"Status: UNDER BUDGET (Remaining: {difference})"
        else:
            result += f"Status: OVER BUDGET (Deficit: {abs(difference)})"
            
        return result
    except Exception as e:
        return f"Cost estimator failed: {str(e)}"

@tool
def currency_tool(base_currency: str, target_currency: str) -> str:
    """
    Currency Tool: Gets live exchange rates to convert from a base currency (e.g., USD) to a target currency (e.g., PKR).
    Returns the exchange rate and a quick conversion example.
    """
    try:
        api_key = _get_env_key("EXCHANGERATE_API_KEY")
        base_currency = base_currency.upper()
        target_currency = target_currency.upper()
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("result") != "success":
            return f"Currency tool failed: Could not fetch data for {base_currency}."
            
        rates = data.get("rates", {})
        if target_currency not in rates:
            return f"Currency tool failed: Rate for {target_currency} not available."
            
        rate = rates[target_currency]
        return f"1 {base_currency} is equal to {rate} {target_currency}."
    except Exception as e:
        return f"Currency tool failed: {str(e)}"

# List of tools to be bound to the LLM
get_tools = [search_tool, places_tool, weather_tool, routing_tool, cost_estimator, currency_tool]
