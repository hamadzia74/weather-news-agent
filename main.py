"""
My first AI agent - a weather and news bot.

Run it with:   python main.py

It uses the OpenAI Agents SDK, but runs on FREE models through OpenRouter,
so it does not cost anything.

An "agent" is three simple things put together:
  1. tools         -> what it is allowed to do        (part 1 below)
  2. instructions  -> how it should behave            (part 2 below)
  3. a model       -> the AI brain that picks a tool  (part 2 below)

We never call the tools ourselves. We hand them to the agent,
and the model decides which one to use based on what you ask.
"""

import asyncio
import os
import sys
import xml.etree.ElementTree as ET

import requests
from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Read the .env file so we can get our API key out of it.
load_dotenv()

# The SDK normally uploads a report of every run to OpenAI's dashboard, and that
# needs a PAID OpenAI key. We are not using OpenAI, so we switch it off.
# Without this line you get "OPENAI_API_KEY is not set" warnings.
set_tracing_disabled(True)


#  PART 1: THE TOOLS
# A tool is just a normal Python function. Nothing magic.
# The model reads three things to decide when to use one:
#   - the NAME          -> get_weather
#   - the DOCSTRING     -> tells it WHEN to use the tool
#   - the TYPE HINT     -> city: str tells it WHAT to pass in
# So the docstrings below are instructions for the AI, not just comments.
# ============================================================

# Open-Meteo sends the weather as a number code. This turns it into words.
WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "cloudy",
    45: "foggy", 48: "foggy", 51: "light drizzle", 53: "drizzle",
    55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
    81: "rain showers", 82: "heavy rain showers", 95: "thunderstorm",
}


def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The name of the city, for example "Pune" or "London".
    """
    # Step 1: turn the city name into map coordinates (latitude / longitude).
    search = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=15,
    ).json()

    if not search.get("results"):
        return f"Sorry, I could not find a city called '{city}'."

    place = search["results"][0]

    # Step 2: ask for the weather at those coordinates.
    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,weather_code",
        },
        timeout=15,
    ).json()["current"]

    sky = WEATHER_CODES.get(weather["weather_code"], "unclear skies")

    # Step 3: send a plain sentence back to the model.
    return (
        f"Weather in {place['name']}, {place.get('country', '')}: "
        f"{weather['temperature_2m']}C, {sky}, "
        f"humidity {weather['relative_humidity_2m']}%."
    )


def get_news(topic: str) -> str:
    """Get the latest news headlines about a topic.

    Args:
        topic: What to search the news for, for example "cricket" or "AI".
    """
    # Google News gives free news in RSS format (a kind of XML). No key needed.
    response = requests.get(
        "https://news.google.com/rss/search",
        params={"q": topic, "hl": "en-US", "gl": "US", "ceid": "US:en"},
        timeout=15,
    )

    # Read the XML and pull out the first 5 <item> blocks.
    items = ET.fromstring(response.text).findall(".//item")[:5]

    if not items:
        return f"I could not find any news about '{topic}'."

    headlines = []
    for item in items:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        headlines.append(f"- {title}\n  {link}")

    return f"Top news about '{topic}':\n" + "\n".join(headlines)


# ============================================================
#  PART 2: THE AGENT
# ============================================================

# A free model that supports tool calling. Change it in your .env file.
# "openrouter/free" auto-picks whichever free model is available right now.
MODEL_NAME = os.getenv("MODEL_NAME", "openrouter/free")


def create_agent():
    """Connect to OpenRouter and build our agent."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    # Also catch the case where the .env file still has the example text in it.
    if not api_key or api_key.startswith("paste-your"):
        sys.exit(
            "No OPENROUTER_API_KEY found.\n"
            "1. Get a free key at https://openrouter.ai/keys\n"
            "2. Open the .env file and replace the placeholder with your key."
        )

    # Point the OpenAI client at OpenRouter's address instead of OpenAI's.
    # This one line is what makes the project free.
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    # Wrap that client as a model the agent can use.
    model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client)

    return Agent(
        name="Buddy",
        instructions=(
            "You are Buddy, a friendly assistant that reports weather and news. "
            "Use the get_weather tool for anything about weather. "
            "Use the get_news tool for anything about news or current events. "
            "Never make up weather or headlines - always use a tool to find out. "
            "Keep your answers short and easy to read."
        ),
        model=model,
        # function_tool() reads each function's name, docstring and type hints,
        # and describes them to the model.
        tools=[function_tool(get_weather), function_tool(get_news)],
    )


# ============================================================
#  PART 3: THE CHAT LOOP
# ============================================================


async def main():
    agent = create_agent()

    print(f"Buddy is ready! (free model: {MODEL_NAME})")
    print("Try asking:")
    print("  - What's the weather in Pune?")
    print("  - Show me news about cricket.")
    print("Type 'exit' to stop.\n" + "-" * 50)

    # This list remembers the conversation so Buddy knows what you said before.
    conversation = []

    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if question.lower() in ("exit", "quit"):
            print("Bye!")
            break

        if not question:
            continue

        print("Thinking...")

        # Add your new question to the conversation, then run the agent.
        conversation.append({"role": "user", "content": question})

        try:
            # This one line does the whole loop:
            # model thinks -> calls a tool -> reads the result -> writes a reply.
            result = await Runner.run(agent, conversation)
        except Exception as error:
            print(f"\nSomething went wrong: {error}")
            print("Tip: free models get busy. Wait a moment, or try a")
            print("different MODEL_NAME in your .env file.")
            conversation.pop()  # forget the failed question
            continue

        # Save everything (your question, the tool calls, Buddy's reply)
        # so the next question still has the full history.
        conversation = result.to_input_list()

        print(f"\nBuddy: {result.final_output}")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
