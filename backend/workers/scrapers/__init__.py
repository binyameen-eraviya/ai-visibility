"""Platform scraper adapters.

One adapter per AI platform (Perplexity, ChatGPT, Gemini, Google AI Overviews,
Copilot), each implementing BasePlatformAdapter. The worker layer only ever
talks to the adapter interface, so any platform can be swapped from browser
scraping to an official API client without touching the rest of the system.
"""
