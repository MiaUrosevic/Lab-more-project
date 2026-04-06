# llm.py
"""
llm.py - Wrapper for LLM with doctests
"""

class LLM:
    """A mock LLM class for testing and doctests."""

    def chat(self, prompt, model="openai/gpt-oss-20b"):
        """Return a fixed response for any user prompt."""
        return "Hello from LLM"

    def chat_with_system(self, system_prompt, user_prompt, model="openai/gpt-oss-20b"):
        """Return a fixed response for system + user prompt."""
        return "Hello from LLM"

    def stream_chat(self, prompt, model="openai/gpt-oss-20b"):
        """Print each character of a fixed response as a stream."""
        response = "Hi!"
        for char in response:
            print(char, end="", flush=True)
        print()
        print()