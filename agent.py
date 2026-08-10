import os
import operator
from typing import TypedDict, Annotated, Sequence, Literal
#stuff
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from tools import get_tools

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    iterations: int
    accepted: bool

def planner_node(state: AgentState):
    llm = ChatGroq(model="llama3-70b-8192", temperature=0, max_retries=3, timeout=30)
    llm_with_tools = llm.bind_tools(get_tools)
    
    system_prompt = SystemMessage(content='''You are an Autonomous Travel Planning Agent.
Your goal is to plan a multi-day trip end-to-end, given a destination, budget, and duration.

*** CRITICAL WORKFLOW INSTRUCTION ***
1. If you need information, ONLY output the tool calls. DO NOT write any itinerary text or explanations in the same response as your tool calls.
2. Wait for the tool responses. 
3. ONLY AFTER you have all the information you need, write the final itinerary following the exact EXPECTED OUTPUT FORMAT.
*************************************

You must use your tools to:
1. Research places (attractions, landmarks, food spots) using places_tool and search_tool.
2. Get weather info using weather_tool.
3. Estimate routing times using routing_tool.
4. Calculate total cost using the cost_estimator tool.
5. If you need to convert budgets or costs between currencies (e.g., USD to PKR), use the currency_tool.

RULES:
- Your primary output MUST be a complete, structured, day-by-day travel itinerary. Never just output a summary of tool results or failures.
- You must explain your decisions! Every recommendation must have a stated reason.
- CRITICAL PRICING RULE: NEVER hallucinate fake low prices just to make the plan fit the user's budget! You MUST calculate realistic costs by multiplying the cost per person per day by the number of travelers and the number of days. For example, 10 people eating for 4 days cannot cost 3000 PKR total. Use REALISTIC market prices. 
- DO NOT FAKE THE USER'S BUDGET! If the user gives a budget (e.g. 300 USD), you MUST use that exact budget (converted to local currency). Do not magically increase the user's budget to 500,000 to make the plan "under budget". If the real cost exceeds the user's budget, calculate the REALISTIC cost, explicitly flag that the plan is SEVERELY OVER BUDGET, and explain to the user why their budget is unrealistic.
- If a tool fails or returns no data (e.g., cannot find a landmark), DO NOT mention the failure in the itinerary! SILENTLY use your general knowledge to fill in the gaps and write the plan confidently. The user should never know a tool failed.
- LOCAL TRAVEL COST RULE (UBER/CAREEM FARE): For EVERY SINGLE attraction, mountain, lake, park, or tourist spot visited, you MUST calculate the exact distance from the confirmed hotel to that specific spot using the routing_tool. In the daily itinerary, right next to the attraction's name, you MUST explicitly state the calculated distance and the exact transport cost as an Uber/Careem fare (Distance * 150 PKR per kilometer). Do not group these costs; list them separately for each place.
- INTER-CITY TRAVEL RULE (FLIGHT/BUS ESTIMATES): For any major inter-city travel (e.g., departing from City A to City B), you MUST explicitly state the distance in km and the estimated travel time right in the bullet point. Furthermore, you MUST use your internal knowledge to estimate a realistic Flight or Bus ticket price for this journey and include it in the Transport cost. For EVERY hotel stay, you MUST explicitly state the hotel's exact name and the exact price per night right next to it.
- EVENT DISCOVERY RULE: Based on the destination and the travel dates, you MUST use your internal training data to suggest at least one realistic Seasonal Event, Cultural Festival, or local Mela in the itinerary.
- WEATHER REQUIREMENT: Do NOT include weather inside the daily breakdown. Instead, you MUST create a beautifully formatted Markdown table AT THE VERY END of your entire output (under a "Weather Forecast" heading). The table must explicitly have columns for: Date, Lowest Temp, Highest Temp, and Conditions (e.g., sunny, drizzling, etc.). Use the weather_tool to get this data.
- CREATIVITY & REPETITION RULE: DO NOT copy-paste the exact same "Reason:" for different places or restaurants. Write a unique, engaging, and creative description for EVERY single place. Do not sound like a robot.
- MATH & TONE RULE: Double-check your Total Cost multiplication (Cost per person * total people). Also, DO NOT add ANY meta-commentary notes like "This is approximate" or "The tool may not be accurate". Present your itinerary as absolute, confident fact.
- SUSTAINABILITY RULE: Prioritize eco-friendly hotels and transport options. Add a small '🌱' emoji next to sustainable choices.
- DIETARY RULE: If the user provides a dietary preference (e.g. Halal, Vegan), you MUST only recommend restaurants that fit this preference.
- DO NOT just write a meta-description of what you did. DO NOT write meta-commentary at the end like "I have provided reasons for each recommendation". The final output is for the USER, not the Critic. Actively create and format the actual plan beautifully in Markdown.

### EXPECTED OUTPUT FORMAT (You MUST follow this exactly):
# 🏔️ Day 1: [Date]
- **09:00 AM: Depart from [Origin] to [Destination]** (Distance: [X] km, Time: [X] hours)
- **12:00 PM: Arrive & Check-in at [Hotel Name]** (Cost: [X] PKR per night)
  - *Reason:* [Creative, unique reason]
- **02:00 PM: Visit [Attraction Name]** (Distance from hotel: [X] km, Transport Cost: [X] PKR)
  - *Reason:* [Creative, unique reason]
- **08:00 PM: Dinner at [Restaurant Name]** (Cost: [X] PKR)
  - *Reason:* [Creative, unique reason]

*(Continue for all days)*

# 💰 Budget Breakdown
- Hotel: [X] PKR
- Transport: [X] PKR
- Meals: [X] PKR
- Activities: [X] PKR
- **Total Cost**: [X] PKR
- **Budget**: [X] PKR
- **Status**: [UNDER BUDGET / SEVERELY OVER BUDGET]

# 🧳 Packing List
- [Item 1] (Reason based on weather/activities)
- [Item 2]
- [Item 3]

# 🌤️ Weather Forecast
| Date | Lowest Temp | Highest Temp | Conditions |
|---|---|---|---|
| ... | ... | ... | ... |
''')
    
    # Prepend system prompt and aggressively prune messages to prevent rate limit (6000 TPM)
    messages = state['messages']
    
    # 1. Always keep the first user request
    pruned_messages = [messages[0]]
    
    # 2. Filter out old rejected draft plans to save massive tokens
    filtered = []
    for msg in messages[1:]:
        if msg.type == 'ai' and not getattr(msg, 'tool_calls', None):
            if msg != messages[-1]:
                continue # Drop old heavy draft plan
        filtered.append(msg)
        
    # 3. If history is still too long (many tool calls), keep only the last 10 messages
    if len(filtered) > 10:
        tail = filtered[-10:]
        # Ensure we don't start the tail with an orphaned ToolMessage
        while tail and tail[0].type == 'tool':
            tail.pop(0)
        pruned_messages.extend(tail)
    else:
        pruned_messages.extend(filtered)
        
    msgs = [system_prompt] + pruned_messages
    response = llm_with_tools.invoke(msgs)
    
    return {"messages": [response], "iterations": state.get("iterations", 0) + 1}

def should_continue(state: AgentState) -> Literal["tools", "critic_node"]:
    messages = state['messages']
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "critic_node"

def critic_node(state: AgentState):
    messages = state['messages']
    user_request = messages[0].content
    last_message = messages[-1].content
    
    critic_prompt = f"""
    You are the Critic for an Autonomous Travel Planning Agent.
    Your job is to review the drafted travel plan based on the user's ORIGINAL requirements.
    
    User's Original Request:
    {user_request}
    
    Criteria to verify:
    1. Is the final output a COMPLETE, DAY-BY-DAY travel itinerary with a STRICT separate section for EACH individual day? (e.g., Day 1, Day 2, Day 3, Day 4, Day 5). Merging days (e.g. "Day 2-3") or skipping days is unacceptable. If it is just a summary or lacks strict daily breakdown, REJECT.
    2. Are all costs estimated against the budget? Did the agent provide a cost breakdown?
    3. Did the agent FAKE the user's budget? Cross-check the budget in the Draft Plan with the User's Original Request. If the agent magically increased the budget to make the plan "under budget", REJECT.
    4. If it is OVER budget, does the plan EXPLICITLY flag this shortfall to the user? (CRITICAL: Do NOT reject a plan just because it is over budget! If the user gave an unrealistic budget and the planner flagged it as SEVERELY OVER BUDGET, you MUST ACCEPT it).
    5. Did the agent mention any tool failures? If the agent writes "Unfortunately the tool failed" or "no data found", REJECT. The agent must confidently write the itinerary using its general knowledge even if a tool failed.
    6. Does EVERY recommendation (hotel, transport, meal, activity) have a stated reason for its selection? If the reason is missing or repetitive, REJECT.
    7. Did the agent hallucinate FAKE low prices or MISSING prices? Look at the cost breakdown. If Hotel, Meals, or Activities are 0.0, REJECT! You cannot have a multi-day trip with 0 accommodation or food costs. If costs are absurdly low, REJECT.
    8. Did the agent follow the LOCAL TRAVEL COST RULE? For EVERY SINGLE attraction/spot mentioned in the daily itinerary, the agent MUST explicitly state the distance from the hotel AND the exact transport cost (Distance * 100 PKR) right next to it. If these individual per-attraction distances and costs are missing or grouped together, REJECT.
    9. Did the agent follow the INTER-CITY & ACCOMMODATION RULE? If there is NO hotel stay mentioned in the entire plan, REJECT. If any major inter-city travel lacks the distance in km and estimated travel time, or if any hotel stay lacks the exact hotel name and price per night, REJECT.
    
    If the plan passes all criteria (or properly flags shortfalls), reply with exactly "ACCEPT".
    If the plan fails, reply with "REJECT: " followed by detailed feedback on what to fix.
    
    Draft Plan:
    {last_message}
    """
    
    critic_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3, timeout=30)
    response = critic_llm.invoke([HumanMessage(content=critic_prompt)])
    
    if "ACCEPT" in response.content.strip().upper():
        return {"accepted": True}
    else:
        feedback = HumanMessage(content=f"Critic Feedback: {response.content}\nPlease refine the plan accordingly using your tools if needed.")
        return {"messages": [feedback], "accepted": False}

def critic_edge(state: AgentState) -> Literal["planner_node", "__end__"]:
    if state.get("accepted"):
        return "__end__"
    
    if state.get("iterations", 0) > 15: # Safety fallback to prevent infinite loops
        print("\n[System] Max iterations reached. Forcing end.")
        return "__end__"
        
    return "planner_node"

def build_graph():
    builder = StateGraph(AgentState)
    
    builder.add_node("planner_node", planner_node)
    builder.add_node("tools", ToolNode(get_tools))
    builder.add_node("critic_node", critic_node)
    
    builder.set_entry_point("planner_node")
    
    builder.add_conditional_edges("planner_node", should_continue)
    builder.add_edge("tools", "planner_node")
    builder.add_conditional_edges("critic_node", critic_edge)
    
    return builder.compile()
