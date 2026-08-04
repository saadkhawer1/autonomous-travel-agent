# Autonomous Travel Planning Agent

This is an autonomous travel planning agent that plans a multi-day trip end-to-end, given a destination, budget, and duration. It researches places, estimates costs, and justifies its recommendations. It includes a Critic/Reflection node to ensure the plan stays within budget and gracefully handles tool failures.

## Setup

1. Create a `.env` file in the root of the project with the following API keys:
```
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
GEOAPIFY_API_KEY=your_geoapify_api_key
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
OPENROUTESERVICE_API_KEY=your_openrouteservice_api_key
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the agent:
```bash
python main.py
```

## Mandatory API Research Component

As part of the requirements, at least three candidate APIs for each core tool function were researched. Below is the documentation of the available features, free tier limits, pricing beyond free tier, authentication method, rate limits, and the justification for the selected APIs.

### 1. Web Search API candidates

*   **Tavily Search API (Selected)**
    *   **Features:** Web search optimized for AI agents, basic/advanced search, content extraction.
    *   **Free Tier:** 1,000 API credits per month (no CC required).
    *   **Pricing:** Pay-as-you-go at $0.008 per credit, or monthly subscriptions starting around $30/month for 4,000 credits.
    *   **Auth:** API Key.
    *   **Rate Limits:** 100 requests per minute (development keys).
    *   **Why Selected:** Tavily is specifically designed for integration with AI agents. The free tier is generous (1,000 credits) and doesn't require complex scraping workarounds.
*   **DuckDuckGo Search (Python `ddgs`)**
    *   **Features:** Web search via scraping.
    *   **Free Tier:** Completely free, but unofficial.
    *   **Pricing:** N/A.
    *   **Auth:** None.
    *   **Rate Limits:** Undefined but heavily rate-limited by anti-bot measures; frequent errors (`RatelimitException`) when making more than a few requests.
    *   **Why Rejected:** Too unstable for a reliable autonomous agent due to frequent blocking.
*   **Serper.dev (Google Search)**
    *   **Features:** Google Search, Places, Images.
    *   **Free Tier:** ~2,500 free queries upon signup.
    *   **Pricing:** Starts at $50/month for 50,000 queries.
    *   **Auth:** API Key.
    *   **Rate Limits:** Generous, generally not an issue for development.
    *   **Why Rejected:** While good, Tavily's monthly recurring 1,000 credits are more sustainable for a free-tier project than a one-time signup bonus.

### 2. Places/Geocoding API candidates

*   **Geoapify Places API (Selected)**
    *   **Features:** Places search by category, geocoding, routing.
    *   **Free Tier:** 3,000 credits per day. (1 simple request = 1 credit).
    *   **Pricing:** Paid plans start at €49/month.
    *   **Auth:** API Key.
    *   **Rate Limits:** Very permissive on the free tier (up to daily limit).
    *   **Why Selected:** Offers an excellent daily free quota (3,000/day) and allows caching of results. It is ideal for an agent that needs to search for multiple categories of places (hotels, restaurants, attractions) per city.
*   **OpenStreetMap / Nominatim**
    *   **Features:** Geocoding and reverse geocoding.
    *   **Free Tier:** Free, donated servers.
    *   **Pricing:** N/A (unless self-hosted or through a third-party provider).
    *   **Auth:** User-Agent string required.
    *   **Rate Limits:** STRICT maximum of 1 request per second. No bulk geocoding allowed.
    *   **Why Rejected:** The 1 request/second limit and ban on bulk usage make it risky for an agent that might make rapid, sequential queries.
*   **Google Places API**
    *   **Features:** The most comprehensive place data globally.
    *   **Free Tier:** $200 monthly credit (covers some usage, but requires billing setup).
    *   **Pricing:** Highly granular; e.g., Place Details can cost up to $0.017 per request.
    *   **Auth:** API Key + Billing Account.
    *   **Rate Limits:** High limits depending on quota settings.
    *   **Why Rejected:** Requires a credit card to activate the $200 free tier, which can result in unexpected charges if the agent loops or over-queries.

### 3. Weather API candidates

*   **OpenWeatherMap (Selected)**
    *   **Features:** Current weather, forecasts, historical data.
    *   **Free Tier:** 1,000,000 calls per month for standard API; 1,000 calls/day for One Call 3.0.
    *   **Pricing:** One Call overages are $0.0015/call. Monthly subscriptions start at $40.
    *   **Auth:** API Key.
    *   **Rate Limits:** 60 calls per minute (Classic free tier).
    *   **Why Selected:** The industry standard for free weather APIs. 60 calls/minute and 1M calls/month on the classic tier are more than enough.
*   **WeatherAPI.com**
    *   **Features:** Forecast, historical, astronomy data.
    *   **Free Tier:** 1,000,000 calls/month (requires attribution).
    *   **Pricing:** Paid tiers start at $4/month.
    *   **Auth:** API Key.
    *   **Rate Limits:** Not explicitly small, but limited history.
    *   **Why Rejected:** OpenWeatherMap has broader community support in Python/LangChain ecosystems, though both are viable.
*   **Open-Meteo**
    *   **Features:** Forecast, historical data, open-source.
    *   **Free Tier:** Unlimited for non-commercial use.
    *   **Pricing:** Paid options for commercial APIs.
    *   **Auth:** None required for free tier.
    *   **Rate Limits:** Varies, but generous for non-commercial.
    *   **Why Rejected:** Excellent choice, but OpenWeatherMap provides slightly more reliable global localized data for obscure tourist attractions.

### 4. Routing/Directions API candidates

*   **OpenRouteService (Selected)**
    *   **Features:** Directions, isochrones, matrix routing.
    *   **Free Tier:** 2,000 directions requests per day.
    *   **Pricing:** Free for standard use; enterprise requires on-premise or special arrangements.
    *   **Auth:** API Key.
    *   **Rate Limits:** 40 directions requests per minute.
    *   **Why Selected:** Generous daily limits (2,000) and completely free standard plan makes it perfect for estimating travel times between attractions in a trip.
*   **Mapbox Directions API**
    *   **Features:** Directions, optimized routing.
    *   **Free Tier:** 100,000 free requests per month.
    *   **Pricing:** ~$2.00 per 1,000 requests after free tier.
    *   **Auth:** API Key.
    *   **Rate Limits:** High limits, but usage-based billing.
    *   **Why Rejected:** Like Google, exceeding the free tier incurs automatic pay-as-you-go costs. OpenRouteService provides a safer, hard-capped free tier.
*   **Google Directions API**
    *   **Features:** Industry-leading routing, transit, real-time traffic.
    *   **Free Tier:** $200 monthly credit shared across Google Maps APIs.
    *   **Pricing:** $5.00 per 1,000 requests.
    *   **Auth:** API Key + Billing Account.
    *   **Rate Limits:** High limits based on billing.
    *   **Why Rejected:** Same reason as Google Places—requires credit card and poses a risk of unexpected charges during development of autonomous agents.
