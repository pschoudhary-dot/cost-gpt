from phi.agent import Agent
from phi.model.openai.like import OpenAILike
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = "your api"
BASE_URL = "yourbaseurl"


Claude=OpenAILike(
    id="claude-3-5-sonnet-20240620",    
    api_key=API_KEY,
    base_url=BASE_URL
)

web_agent = Agent(
    name="Web Agent",
    model=Claude,
    tools=[DuckDuckGo()],
    instructions=["Always include sources"],
    show_tool_calls=True,
    markdown=True,
)
web_agent.print_response("Tell me about OpenAI Sora?")
