import os
import operator
from typing import TypedDict, Annotated, Sequence, Literal

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
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, max_retries=3, timeout=30)
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
- CRITICAL PRICING RULE: NEVER hallucinate fake low prices just to make the plan fit the user's budget! Use REALISTIC market prices for hotels, transport, and food (e.g., a trip to Hunza realistically costs at least 50,000+ PKR). If the user's budget is ridiculously low, calculate the REALISTIC cost, explicitly flag that the plan is SEVERELY OVER BUDGET, and explain to the user why their budget is unrealistic.
- If a tool fails or returns no data, DO NOT stop planning. Gracefully mention the missing data IN the itinerary, but YOU MUST STILL GENERATE THE FULL DAY-BY-DAY ITINERARY based on your general knowledge.
- DO NOT just write a meta-description of what you did. Actively create and format the actual plan beautifully in Markdown.
''')
    
    # Prepend system prompt
    msgs = [system_prompt] + list(state['messages'])
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
    last_message = messages[-1].content
    
    critic_prompt = f"""
    You are the Critic for an Autonomous Travel Planning Agent.
    Your job is to review the drafted travel plan based on the user's requirements.
    
    Criteria to verify:
    1. Is the final output a COMPLETE, DAY-BY-DAY travel itinerary with a STRICT separate section for EACH individual day? (e.g., Day 1, Day 2, Day 3, Day 4, Day 5). Merging days (e.g. "Day 2-3") or skipping days is unacceptable. If it is just a summary or lacks strict daily breakdown, REJECT.
    2. Are all costs estimated against the budget? Did the agent provide a cost breakdown?
    3. If it is OVER budget, does the plan EXPLICITLY flag this shortfall to the user? (CRITICAL: Do NOT reject a plan just because it is over budget! If the user gave an unrealistic budget and the planner flagged it as SEVERELY OVER BUDGET, you MUST ACCEPT it. Do not force the planner to find magical cheap alternatives).
    4. If any tools failed, did the agent gracefully handle it and STILL generate a full day-by-day itinerary? If the agent gave up planning, REJECT.
    5. Does EVERY recommendation (hotel, transport, meal, activity) have a stated reason for its selection?
    
    If the plan passes all criteria (or properly flags shortfalls), reply with exactly "ACCEPT".
    If the plan fails, reply with "REJECT: " followed by detailed feedback on what to fix.
    
    Draft Plan:
    {last_message}
    """
    
    critic_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, max_retries=3, timeout=30)
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
