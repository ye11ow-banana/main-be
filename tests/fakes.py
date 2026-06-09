from unittest.mock import AsyncMock, Mock


class FakeOpenAI:
    def __init__(self):
        self.chat = Mock()
        self.responses = Mock()

        self.chat.completions = Mock()
        self.chat.completions.create = AsyncMock(
            return_value={"choices": [{"message": {"content": "fake response"}}]}
        )
