import os
import sys
import asyncio
import requests
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_DECISIONS_ENDPOINT = "https://openrouter.ai/api/alpha/decisions"

# Using the specific Jev model on OpenRouter
JEV_MODEL = "typesafe/jev-1.14"

#Get the directory where router.py lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Point to mcp_server.py one level up in the parent directory
MCP_SERVER_PATH = os.path.join(BASE_DIR, "..", "mcp_server.py")



def triage_request(user_prompt: str) -> str:
    """Uses Jev via OpenRouter to decide the routing path."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # OpenRouter's Decisions API separates the state (context) from the questions
    payload = {
        "model": JEV_MODEL,
        "state": f"User prompt: {user_prompt}",
        "questions": {
            "routing_decision": {
                "type": "choice",
                "instructions": "Evaluate the user's prompt as a strict routing system.",
                "criteria": {
                    "requires_llm": "The user asks for an explanation, analysis, troubleshooting steps, or readable text generation.",
                    "requires_jev": "The user is ONLY asking to categorize data into a predefined list and requires no explanation."
                }
            }
        }
    }
    
    response = requests.post(OPENROUTER_DECISIONS_ENDPOINT, json=payload, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    
    # OpenRouter returns answers nested under the question key you provided
    answer = result.get("answers", {}).get("routing_decision", {})
    confidence = answer.get("confidence", 0.0)
    chosen_route = answer.get("choice", "requires_llm")
    
    print(f"[Router] Selected Path: {chosen_route} (Confidence: {confidence:.2f})")
    
    if confidence < 0.75:
        print("[Router] Confidence too low. Defaulting to LLM.")
        return "requires_llm"
        
    return chosen_route

async def call_project_backend_llm(user_prompt: str):
    """Acts as the MCP Client. Boots up the MCP server and triggers the backend LLM tool."""
    print("[Agent] Spinning up MCP Server connection...")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER_PATH]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[Agent] Connected. Triggering 'trigger_backend_llm' tool...")
            
            result = await session.call_tool(
                "trigger_backend_llm", 
                arguments={"prompt": user_prompt}
            )
            return result.content[0].text

def run_jev_strict_categorization(user_prompt: str):
    """The secondary Jev branch bypassing the LLM, routed through OpenRouter."""
    print("[Agent] Asking Jev for strict categorization...")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": JEV_MODEL,
        "state": f"User prompt: {user_prompt}",
        "questions": {
            "ticket_category": {
                "type": "choice",
                "instructions": "Categorize the provided ticket.",
                "criteria": {
                    "Bug": "Software defects, broken features, or error messages.",
                    "Feature Request": "Ideas for new functionality or improvements.",
                    "General Inquiry": "Questions about usage, billing, or general help."
                }
            }
        }
    }
    
    response = requests.post(OPENROUTER_DECISIONS_ENDPOINT, json=payload, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    choice = result.get("answers", {}).get("ticket_category", {}).get("choice", "Unknown")
    
    return f"[Jev Execution] Categorized as: {choice}"

async def main_agent_loop(user_prompt: str):
    print(f"\n--- New Request: '{user_prompt}' ---")
    
    route = triage_request(user_prompt)
    
    if route == "requires_llm":
        final_answer = await call_project_backend_llm(user_prompt)
        print(f"\nFinal Output:\n{final_answer}")
    elif route == "requires_jev":
        final_answer = run_jev_strict_categorization(user_prompt)
        print(f"\nFinal Output:\n{final_answer}")

if __name__ == "__main__":
    # Test the async loop
    asyncio.run(main_agent_loop("What is the severity of this database connection error, and how do I fix it?"))
    asyncio.run(main_agent_loop("Sort this ticket: 'The login page is returning a 500 error'."))