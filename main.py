import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent import build_graph

def main():
    # Load environment variables (API keys)
    load_dotenv()
    
    # Optional check to verify critical keys exist
    required_keys = ["GEMINI_API_KEY", "TAVILY_API_KEY", "GEOAPIFY_API_KEY", "OPENWEATHERMAP_API_KEY", "OPENROUTESERVICE_API_KEY"]
    missing = [k for k in required_keys if not os.environ.get(k)]
    if missing:
        print(f"Warning: The following API keys are missing in the environment: {', '.join(missing)}")
        print("The agent will likely fail when attempting to use tools requiring these keys.")
        print("Please add them to a .env file and restart.")
        return

    graph = build_graph()
    
    user_input = "Plan a 5-day trip to Hunza under PKR 20,000"
    print(f"Using default prompt: {user_input}")
        
    print("\n--- Starting Autonomous Travel Planner ---\n")
    
    # Execute the graph
    inputs = {"messages": [HumanMessage(content=user_input)], "iterations": 0}
    
    for event in graph.stream(inputs, stream_mode="values"):
        messages = event.get("messages", [])
        if not messages:
            continue
            
        latest_message = messages[-1]
        
        # Print AI messages and tool calls for visibility
        if hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
            print("\n[Agent] is calling tools...")
            for tc in latest_message.tool_calls:
                print(f"  -> Tool: {tc['name']} | Args: {tc['args']}")
        elif latest_message.content and isinstance(latest_message.content, str) and not latest_message.content.startswith("Critic Feedback"):
            if latest_message.type == "ai":
                print(f"\n[Agent Output]:\n{latest_message.content[:500]}... (truncated for preview)\n")
        
        # Print Critic Feedback specifically
        if latest_message.content and isinstance(latest_message.content, str) and latest_message.content.startswith("Critic Feedback"):
            print(f"\n[Critic Node]: {latest_message.content}\n")
            
    print("\n--- Execution Finished ---")

if __name__ == "__main__":
    main()
