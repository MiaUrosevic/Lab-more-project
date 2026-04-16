from chat import parse_args


def test_parse_args_message():
    args = parse_args(["hello"])
    assert args.message == "hello"
    assert args.provider == "groq"
    assert args.debug is False


def test_parse_args_all_flags():
    args = parse_args(["--debug", "--provider", "openai", "hello"])
    assert args.debug is True
    assert args.provider == "openai"
    assert args.message == "hello"
