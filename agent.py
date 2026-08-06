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
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3, timeout=30)
    llm_with_tools = llm.bind_tools(get_tools)
    
    system_prompt = SystemMessage(content='''You are an Autonomous Travel Planning Agent.
Your goal is to plan a multi-day trip end-to-end, given a destination, budget, and duration.
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
- LOCAL TRAVEL COST RULE: For any travel inside a city (e.g., from a hotel to a tourist spot), you MUST calculate the distance using the routing_tool in kilometers and multiply it by 100 PKR per kilometer to estimate the local transport cost. Include this in your cost breakdown.
- WEATHER REQUIREMENT: Do NOT include weather inside the daily breakdown. Instead, you MUST create a beautifully formatted Markdown table AT THE VERY END of your entire output (under a "Weather Forecast" heading). The table must explicitly have columns for: Date, Lowest Temp, Highest Temp, and Conditions (e.g., sunny, drizzling, etc.). Use the weather_tool to get this data.
- DO NOT just write a meta-description of what you did. DO NOT write meta-commentary at the end like "I have provided reasons for each recommendation". The final output is for the USER, not the Critic. Actively create and format the actual plan beautifully in Markdown.
''')
    
    # Prepend system prompt and prune old heavy messages to prevent rate limit (6000 TPM)
    messages = state['messages']
    pruned_messages = [messages[0]]
    for msg in messages[1:]:
        # If it's an AI message with a large drafted plan (no tool calls), and it was rejected, drop it to save tokens
        if msg.type == 'ai' and not getattr(msg, 'tool_calls', None) and len(msg.content) > 500:
            if msg != messages[-1]:
                continue
        pruned_messages.append(msg)
        
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
    6. Does EVERY recommendation (hotel, transport, meal, activity) have a stated reason for its selection?
    7. Did the agent hallucinate FAKE low prices? Look at the cost breakdown and consider the number of people and days. If the cost for hotels, meals, or transport is absurdly low (e.g., 3000 PKR for 10 people over 4 days), REJECT it and force the agent to use realistic market prices, even if it goes severely over budget.
    8. Did the agent follow the LOCAL TRAVEL COST RULE? Any local intra-city travel (e.g. hotel to attraction) MUST be priced at 100 PKR per kilometer using the routing_tool distance. If not, REJECT.
    
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
