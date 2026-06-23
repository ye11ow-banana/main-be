import json
from unittest.mock import AsyncMock, Mock


class FakeOpenAI:
    def __init__(self):
        self.chat = Mock()
        self.responses = Mock()

        self.chat.completions = Mock()
        self.chat.completions.create = AsyncMock(
            return_value={"choices": [{"message": {"content": "fake response"}}]}
        )
        self.responses.create = Mock(side_effect=self._create_response)

    @staticmethod
    def _create_response(**kwargs):
        schema_name = kwargs["text"]["format"]["name"]
        output_data = (
            {"products": []}
            if schema_name == "unknown_to_nutrition"
            else {"items": [], "warnings": [], "unparsed": []}
        )
        return Mock(output_text=json.dumps(output_data))
