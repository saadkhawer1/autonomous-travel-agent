import os
import json
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Import our LangGraph agent
from agent import build_graph

load_dotenv()

app = FastAPI(title="Autonomous Travel Planner API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/plan")
async def plan_trip(request: Request, query: str):
    """
    Server-Sent Events endpoint that streams the agent's progress.
    """
    async def event_generator():
        # Initialize graph
        graph = build_graph()
        inputs = {"messages": [HumanMessage(content=query)], "accepted": False}
        
        # We need to run graph.stream in a thread or asynchronously if possible
        # Since LangGraph stream is synchronous by default, we'll iterate it
        # Note: In a production app, use graph.astream
        try:
            for event in graph.stream(inputs, stream_mode="values"):
                if await request.is_disconnected():
                    break
                
                messages = event.get("messages", [])
                if not messages:
                    continue
                
                latest_message = messages[-1]
                
                # Check for tool calls
                if hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
                    for tc in latest_message.tool_calls:
                        yield {
                            "data": json.dumps({
                                "type": "tool",
                                "name": tc["name"],
                                "args": tc["args"]
                            })
                        }
                        
                # Check for Critic Feedback
                elif latest_message.content and isinstance(latest_message.content, str) and latest_message.content.startswith("Critic Feedback"):
                    yield {
                        "data": json.dumps({
                            "type": "critic",
                            "content": latest_message.content
                        })
                    }
                    
                # General AI output (status/thinking)
                elif latest_message.content and isinstance(latest_message.content, str) and latest_message.type == "ai":
                    yield {
                        "data": json.dumps({
                            "type": "log",
                            "content": latest_message.content[:200] + "..." if len(latest_message.content) > 200 else latest_message.content
                        })
                    }
                    
                # Small pause to ensure SSE flush
                await asyncio.sleep(0.1)
                
            # Send the final complete plan
            if messages:
                final_content = messages[-1].content
                yield {
                    "data": json.dumps({
                        "type": "result",
                        "content": final_content
                    })
                }
                
        except Exception as e:
            yield {
                "data": json.dumps({
                    "type": "critic",
                    "content": f"API Error or Rate Limit: {str(e)}"
                })
            }

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
