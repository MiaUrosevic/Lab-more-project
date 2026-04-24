"""
The compact tool summarizes the current chat history into a short replacement message.
"""


def run_compact(chat):
    """
    Replace the current chat history with a compact summary.

    >>> class DummyChat:
    ...     def __init__(self):
    ...         self.messages = [
    ...             {"role": "user", "content": "hello"},
    ...             {"role": "assistant", "content": "hi there"}
    ...         ]
    ...         self.provider = "groq"
    ...         self.debug = False
    >>> chat = DummyChat()
    >>> result = run_compact(chat)
    >>> result.startswith("Summary of conversation:")
    True
    >>> len(chat.messages)
    1
    >>> chat.messages[0]["role"]
    'system'
    >>> "hello" in chat.messages[0]["content"]
    True
    """
    transcript = []
    for msg in chat.messages:
        transcript.append(f"{msg['role']}: {msg['content']}")
    transcript_text = "\n".join(transcript)

    summary = f"Summary of conversation:\n{transcript_text[:300]}"
    chat.messages = [{"role": "system", "content": summary}]
    return summary
