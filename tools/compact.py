"""
The compact tool summarizes the current chat history into a short replacement message.
"""


def run_compact(chat):
    """
    Replace the current chat history with a compact summary.

    >>> class DummyChat:
    ...     def __init__(self):
    ...         self.messages = [{"role": "user", "content": "hello"}]
    ...         self.provider = "groq"
    ...         self.debug = False
    >>> chat = DummyChat()
    >>> result = run_compact(chat)
    >>> result.startswith("Summary of conversation:")
    True
    >>> chat.messages[0]["role"]
    'system'
    """
    # this is the correct way to turn a 
    # list of dictionaries into a string
    transcript = json.dumps(chat.messages)


    # below is not a correct implmentation;
    # you need to actually use the llm somehow,
    # which you are not.
    summary = f"Summary of conversation:\n{transcript_text[:300]}"
    chat.messages = [{"role": "system", "content": summary}]
    return summary
