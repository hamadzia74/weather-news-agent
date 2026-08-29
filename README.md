# My First AI Agent — Weather & News Bot (100% Free)

A chatbot called **Buddy** that tells you the real weather and the real news.
Built with the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/),
running on **free models via OpenRouter** — no paid account needed.

Everything is in one file: [main.py](main.py).

```
weather-news-agent/
  .venv/              your installed libraries (not shared)
  .env                your real API key (not shared, never commit this)
  .env.example        template showing which keys are needed
  .gitignore          files git should ignore
  main.py             the whole project
  requirements.txt    what to install
  README.md           this file
```

---

## What is an "agent"?

A normal chatbot can only talk. Ask it "what's the weather in Pune?" and it
either guesses or says it doesn't know.

An **agent** is a chatbot we also give some **tools** (normal Python
functions). Now it can go and find things out.

The key idea: **we never decide which tool to use. The model does.**

```
You: "What's the weather in Pune?"
        |
        v
   [ The model reads your question ]
        |
        | "This is about weather. I'll call get_weather with city='Pune'."
        v
   [ The SDK runs our Python function get_weather("Pune") ]
        |
        | returns: "Weather in Pune, India: 25.6C, light drizzle, humidity 76%."
        v
   [ The model reads that and writes a friendly reply ]
        |
        v
Buddy: "It's 25.6C in Pune with light drizzle. Take an umbrella!"
```

That whole loop is one line of code: `await Runner.run(agent, conversation)`.

---

## Setup

**1. Create a virtual environment** (a private folder for this project's libraries):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**2. Install the libraries:**

```powershell
pip install -r requirements.txt
```

**3. Get your free key** at https://openrouter.ai/keys — sign in with Google,
click "Create Key". No card needed.

**4. Create your `.env` file** by copying the template, then paste your key in:

```powershell
copy .env.example .env
```

Open the new `.env` and replace the placeholder:

```
OPENROUTER_API_KEY=sk-or-v1-your-real-key-here
MODEL_NAME=openrouter/free
```

`.env` is listed in `.gitignore`, so your key never gets committed to git.
`.env.example` **is** committed — it's the template that tells anyone cloning
this repo which keys they need, without exposing yours.

**5. Run it:**

```powershell
python main.py
```

```
Buddy is ready! (free model: openrouter/free)
Try asking:
  - What's the weather in Pune?
  - Show me news about cricket.
Type 'exit' to stop.
--------------------------------------------------

You: what's the weather in Pune?
Thinking...

Buddy: The weather in Pune is currently 25.1°C with light drizzle and 78% humidity.
--------------------------------------------------
```

---

## Prompt examples

Things to try, and what each one teaches you.

### 1. Weather questions → calls `get_weather`

```
What's the weather in Pune?
Is it raining in London right now?
How humid is it in Dubai?
Should I carry an umbrella in Mumbai today?
Compare the weather in Delhi and Bangalore.
```

That last one is worth watching. The agent calls `get_weather` once per city,
then compares the answers itself — we never wrote any comparison code:

```
You: Compare the weather in Delhi and Bangalore.

Buddy:
| City      | Temp   | Conditions | Humidity |
|-----------|--------|------------|----------|
| Delhi     | 35.2°C | Cloudy     | 49%      |
| Bangalore | 25.9°C | Drizzle    | 63%      |

Quick take:
- Delhi is significantly hotter (~9°C warmer) and drier.
- Bangalore is cooler...
```

Behind the scenes it actually called the tool **three** times:
`get_weather(Delhi)`, `get_weather(Bangalore)`, then `get_weather(Bengaluru)` —
it double-checked using the city's other name. Agents do things like that on
their own, which is both the fun and the tricky part.

### 2. News questions → calls `get_news`

```
Any news about cricket?
What's happening with AI regulation?
Show me the latest on the Indian economy.
Give me 3 headlines about space exploration.
```

### 3. Both tools in one question

```
Give me a morning briefing for Mumbai.
What's the weather in Pune and any news from Pune?
I'm flying to London tomorrow - weather and headlines please.
```

Here the model works out on its own that it needs **two different tools**,
calls both, and merges the results into one reply:

```
You: Give me a morning briefing for Mumbai.

Buddy: **Morning Briefing for Mumbai**
Weather: 28.3°C, light drizzle, humidity 78%

Top News Headlines:
- Mumbai milk prices jump ₹9, sparking social media reactions
- Doctor on Kailash Mansarovar Yatra goes missing in Nepal
- Mumbai court denies bail to stu...
```

Tools called: `get_weather(Mumbai)` then `get_news(Mumbai)`. This is the moment
an agent stops feeling like a chatbot.

### 4. Follow-up questions (it remembers)

Buddy keeps the conversation, so you don't have to repeat yourself:

```
You: What's the weather in Pune?
Buddy: The weather in Pune is currently 25.1°C with light drizzle and 78% humidity.

You: What about Mumbai?
Buddy: Mumbai: 28.3 °C, light drizzle, humidity 78%.
```

Notice the second question never says the word "weather" — but Buddy still
called `get_weather("Mumbai")`, because it could see the earlier turn. Try
`Any news from there?` next and watch it work out that "there" means Mumbai.

This works because of `conversation = result.to_input_list()` in Part 3.
Delete that line and Buddy forgets everything after every message.

### 5. Questions with no tool → it just answers

```
Hello!
What can you do?
Explain what an API is.
```

The model is smart enough not to call a tool when it doesn't need one.

### 6. Questions that show the limits

```
What was the weather in Pune last Tuesday?
What will the weather be next month?
```

Our `get_weather` only fetches the weather **right now** — it has no history and
no forecast. A good agent will say so. A weaker free model may make something
up, which is a useful lesson: **the agent can only be as good as its tools.**
Want forecasts? Add a `days` argument to `get_weather` and describe it in the
docstring.

### Quick reference

| You say | Tool it picks |
| --- | --- |
| anything about temperature, rain, humidity, "should I wear a jacket" | `get_weather` |
| anything about headlines, news, "what's happening with X" | `get_news` |
| "briefing", "weather and news", a place + both topics | **both** |
| greetings, general questions | none — it just replies |

You never write any of this routing logic. The model decides purely from the
function names, docstrings and type hints in Part 1 of `main.py`.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'requests'` (or `agents`, or `openai`)

Your virtual environment is not activated, so Python is looking in the wrong
place for the libraries. Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should change to `(.venv) PS D:\office\news-weather-app>`. That
`(.venv)` prefix is how you know it worked. **You have to do this every time
you open a new terminal.**

If you get *"running scripts is disabled on this system"*, Windows is blocking
the activate script. Allow it for this terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Or skip activating altogether by naming the venv's Python directly — this
always works:

```powershell
.\.venv\Scripts\python.exe main.py
```

**In VS Code:** press `Ctrl+Shift+P`, choose "Python: Select Interpreter", and
pick the one inside `.venv`. After that, new terminals activate it for you.

### `No OPENROUTER_API_KEY found`

Open `.env` and replace `paste-your-openrouter-key-here` with your real key
from https://openrouter.ai/keys

### `404 - This model is unavailable for free`

The free version of that model was retired. Set `MODEL_NAME=openrouter/free`
in `.env` — that auto-picks a working free model, so it doesn't go stale.

### Error 429, or "rate limit"

Either that model is busy, or you've used your daily free allowance. Wait a
moment and try again, or switch `MODEL_NAME` in `.env` to another free model.

### Buddy answers but never uses the tools

Your model probably doesn't support tool calling. Switch `MODEL_NAME` to one
from the table below.

---

## Why this is free

The Agents SDK is made by OpenAI, but it is **not locked to OpenAI**. It can
talk to any provider using the same message format. We use
[OpenRouter](https://openrouter.ai), which offers several models for free.

Two things in `main.py` make this work:

**1. Point the client at OpenRouter instead of OpenAI**

```python
client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",   # <- the only real change
)

model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client)
```

**2. Turn off tracing**

```python
set_tracing_disabled(True)
```

By default the SDK uploads a report of every run to OpenAI's dashboard, and
that upload needs a **paid** OpenAI key. We're not using OpenAI, so we switch
it off. Skip this line and you get `OPENAI_API_KEY is not set` warnings.

### Careful: not every OpenRouter model is free

A model is only free if its name **ends with `:free`**. Names like
`openai/gpt-4o-mini` are the real paid models, just accessed through OpenRouter.

It must also **support tool calling**, or the agent will chat but never use
your tools. These are tested and working:

| Put this in your `.env` | Notes |
| --- | --- |
| `openrouter/free` | **The default.** Not one model — a router that auto-picks whichever free model is working today. Best choice, because it doesn't break when a model is retired. |
| `minimax/minimax-m3:free` | A specific model. Huge context, good at tools. |
| `nvidia/nemotron-3.5-lightning:free` | A specific model. Fast. |

**Free models get retired often.** If you pin a specific one, sooner or later
you'll see:

```
Error code: 404 - This model is unavailable for free.
```

That's why `openrouter/free` is the default. To find current free models
yourself, filter OpenRouter's list by tool support:
https://openrouter.ai/models?supported_parameters=tools

Free tiers are also rate limited. A `429` means "this model is busy right now" —
wait a moment, or switch `MODEL_NAME`.

---

## How the code works

`main.py` is in three parts.

### Part 1 — The tools

A tool is just a normal function:

```python
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The name of the city, for example "Pune" or "London".
    """
    ...
    return "Weather in Pune, India: 25.6C, light drizzle, humidity 76%."
```

The model reads **three** things to decide when to use it:

- the **name** — `get_weather`
- the **docstring** — tells it *when* to use the tool
- the **type hint** — `city: str` tells it *what* to pass in

So write clear docstrings. They are instructions for the AI, not just comments.

### Part 2 — The agent

```python
agent = Agent(
    name="Buddy",
    instructions="You are Buddy... always use a tool, never guess.",
    model=model,
    tools=[function_tool(get_weather), function_tool(get_news)],
)
```

- `instructions` — the agent's personality and rules (its "system prompt")
- `model` — the free OpenRouter model we set up above
- `tools` — the list of things it's allowed to do

`function_tool()` reads a function's name, docstring and type hints and turns
them into a description the model understands.

> Most tutorials write `@function_tool` directly above the function instead.
> Same result — but keeping it separate means you can still call
> `get_weather("Pune")` yourself to test it (see below).

### Part 3 — The chat loop

```python
conversation.append({"role": "user", "content": question})
result = await Runner.run(agent, conversation)
conversation = result.to_input_list()
print(result.final_output)
```

- `Runner.run` does the whole think → call tool → think again loop.
- `result.final_output` is Buddy's final text reply.
- `result.to_input_list()` gives back the full history, so the next question
  remembers the last one. Without this line Buddy forgets everything after
  every message.
- It's `async`, so `main()` is an `async def` and we start it with
  `asyncio.run(main())` at the bottom of the file.

---

## Testing a tool on its own

Handy when something breaks — this uses no AI and costs nothing:

```powershell
python -c "from main import get_weather; print(get_weather('Pune'))"
python -c "from main import get_news; print(get_news('cricket'))"
```

If these work but the chat doesn't, the problem is your key or your model.
If these fail, it's your internet.

---

## The APIs used (both free, no key needed)

- **Weather** — [Open-Meteo](https://open-meteo.com/). We look up the city's
  latitude/longitude first, then ask for the weather there.
- **News** — Google News RSS. It returns XML, so we use Python's built-in
  `xml.etree.ElementTree` to pull out the headlines.

Free weather API + free news API + free model = the project costs nothing.

---

## Other free options

If OpenRouter is slow or busy, the same two lines swap to any of these — only
the `base_url`, the key, and the model name change:

| Provider | `base_url` | Notes |
| --- | --- | --- |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai/` | Generous free tier, fast, good at tools. Key from [AI Studio](https://aistudio.google.com/apikey). |
| **Groq** | `https://api.groq.com/openai/v1` | Extremely fast. Free tier with rate limits. |
| **Ollama** (your own PC) | `http://localhost:11434/v1` | Fully offline and unlimited, but needs a decent computer. Use `api_key="ollama"`. |

---

## Try this next

1. **Add a third tool.** Write a function in Part 1, then add
   `function_tool(get_time)` to the `tools=[...]` list in Part 2. That's it —
   the model works out the rest. A good first one:

   ```python
   def get_time() -> str:
       """Get the current date and time."""
       from datetime import datetime
       return datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
   ```

2. **Change the personality.** Edit `instructions` — make Buddy reply in Hindi,
   or only in emojis, or as a pirate.

3. **Ask something that needs both tools**, like *"Give me a morning briefing
   for Mumbai"*. Watch it call `get_weather` **and** `get_news` on its own.

4. **Try a different free model.** Change `MODEL_NAME` and see which ones pick
   the right tool. Smaller models often answer without calling anything — that
   alone teaches a lot about why model choice matters for agents.
