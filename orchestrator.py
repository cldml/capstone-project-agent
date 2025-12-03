import os
import logging
import requests
import json
from typing import List,Dict,Any,Optional
from dotenv import load_dotenv

from google import genai
from google.genai import types

from twilio_tool import  TwilioNotifierTool
from calendar_tool import CalendarEventTool

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

GEMINI_MODEL = 'gemini-2.5-flash'
LEARNER_PHONE_NUMBER = os.environ.get('LEARNER_PHONE_NUMBER')
GITHUB_MCP_URL = os.environ.get('GITHUB_MCP_URL', 'http://localhost:8000/recommendation')

class GitHubMcpClient:
    """Client to call the external Github MCP tool """

    def __init__(self,base_url : str):
        self.url = base_url

    def get_top_github_recommendations(self,event_title: str,max_results: int =3) -> List[Dict[str,any]]:
        """
        Retrieves, scores, and ranks the top GitHub repositories for a given learning event title.
        
        The repository ranking is based on a scoring system that prioritizes hands-on content 
        (like tutorials and examples) over just star count.
        """

        logger.info(f"Calling Github MCP for event: {event_title}")

        try:
            response = requests.get(
                self.url,
                params={'event_title': event_title, 'max_results': max_results}
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling GitHub MCP: {e}")

SYSTEM_PROMPT = """
You are a dedicated AI Learning Planner. Your purpose is to ensure the user maximizes their daily learning opportunities.
Action Flow: 1. Call get_today_events. 2. Based on event titles, call get_top_github_recommendations for resources. 3. Synthesize the results. 4. Call send_sms_notification as the final action.
Constraints: The final message must be concise (<300 chars) and cite the top 1-2 GitHub resources.
"""

# Initialize tool instances

try:
    calendar_tool = CalendarEventTool()
    twilio_tool = TwilioNotifierTool()
    github_tool_client = GitHubMcpClient(base_url=GITHUB_MCP_URL)
except Exception as e:
    logger.critical(f"Tool Initialization Failed: {e}")
    exit()

# Map tool names to their execution functions
TOOL_EXECUTOR_MAP = {
    'get_today_events': calendar_tool.get_today_events,
    'get_top_github_recommendations': github_tool_client.get_top_github_recommendations,
    'send_sms_notification': twilio_tool.send_sms_notification,
}


def run_agent():

    client = genai.Client()                   
    tools_list = [
        calendar_tool.get_today_events,
        github_tool_client.get_top_github_recommendations,
        twilio_tool.send_sms_notification
    ]

    initial_prompt = (
        f"Generate today's complete learning schedule, find relevant hands-on resources, "
        f"and send the final message to the learner at {LEARNER_PHONE_NUMBER}."
    )

    session = client.chats.create(
        model= GEMINI_MODEL,
        config=types.GenerateContentConfig(
            tools=tools_list,
            system_instruction=SYSTEM_PROMPT
        )
    )

    # send the initial request
    response = session.send_message(initial_prompt)

    # Tool execution loop
    for _ in range(15):
        if response.function_calls:
            tool_responses = []

            for call in response.function_calls:
                tool_name = call.name
                args=dict(call.args)
                
                tool_func=TOOL_EXECUTOR_MAP.get(tool_name)

                if tool_func:
                    try:
                        tool_result = tool_func(**args)
                        logger.info(f"Executed {tool_name}. Result: {json.dumps(tool_result)[:100]}...")
                        tool_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response=tool_result
                        ))
                        if tool_name == 'send_sms_notification':
                            logger.info("Final SMS notification successfully triggered by the agent.")
                            return f"Plan successfully sent to {LEARNER_PHONE_NUMBER}."

                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        tool_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response={"error": str(e), "status": "failed"}
                        ))
                else:
                    logger.warning(f"Tool {tool_name} not found in map.")

        else:
            final_text = response.text
            logger.info(f"Agent finished planning. Final response:\n{final_text}")
            return final_text
    
    logger.error("Agent exceeded the maximum loop iterations.")
    return "Agent planning failed: Loop iteration limit exceeded."

if __name__ == "__main__":
    logger.info("--- Starting ADK-Style Learning Agent Orchestration ---")
    final_output = run_agent()
    logger.info(f"Final Agent Status: {final_output}")
    logger.info("--- Orchestration Complete ---")    