import base64
import json
from typing import Any

from openai import OpenAI

from calorie.models import (
    OpenAIProductCreationListResponseDTO,
    OpenAIProductListResponseDTO,
)
from calorie.openai_client.openai_schemas import (
    ITEMS_SCHEMA,
    UNKNOWN_TO_NUTRITION_SCHEMA,
)


class CalorieOpenAIClient:
    def __init__(self, client: OpenAI):
        self._client = client

    def image_to_items(
        self, image_bytes: bytes, mime: str, model: str
    ) -> OpenAIProductListResponseDTO:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime};base64,{b64}"

        prompt = """
        You are extracting a handwritten food table.

        Task:
        1) Identify ONLY the product column headers (top row of the table). Headers are Ukrainian product names.
        2) Identify two user rows:
           - Row labeled 'М' = ye11ow_banana
           - Row labeled 'А' = kaminchyk
        3) For each header, read values ONLY from the cell in ye11ow_banana row and kaminchyk row under that header.
        4) ye11ow_banana row or kaminchyk row can be empty under each header. If both of them are empty in a header, skip that header.

        Rules:
        - A cell can contain:
          - A single integer in grams (e.g., "40")
          - A sum of integers in grams written as math (e.g., "40+59" or "40+60+50")
        - If the cell contains math, keep it exactly as written (do NOT calculate it).
        - Output ONLY items that are clearly in grams (integers or integer sums).
        - If a value is unclear, skip it and add it to warnings.
        - Do NOT read totals or notes outside the grid.
        - Return JSON strictly by schema.
        """

        # noinspection PyTypeChecker
        response = self._client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "image_to_items",
                    "strict": True,
                    "schema": ITEMS_SCHEMA,
                }
            },
        )
        return OpenAIProductListResponseDTO.model_validate(
            self._response_to_json(response)
        )

    def user_text_to_items(
        self, user_text: str, model: str
    ) -> OpenAIProductListResponseDTO:
        prompt = f"""
        Parse user's text into food items with grams.

        Input format may contain multiple persons:
        - "А:" means kaminchyk
        - "М:" means ye11ow_banana
        Everything after a person tag belongs to that person until the next tag.

        Return items with:
        - raw_name: ONLY the base product/dish name for DB matching (remove size/flavor/brand/extra descriptors)

        Rules for raw_name:
        - Remove sizes/amounts: "30 см", "20 см", "1 л", "500 мл", "200 г", "грам 200", etc.
        - Remove brands: "кока кола", "coca-cola", "pepsi" -> canonical "кола"
        - Remove flavors/variants: "гавайська", "з шинкою", "кебаб курячий" -> canonical "кебаб"
        - Keep only the core noun (single base item). Examples:
          - "піца 30 см гавайська" -> canonical_name="піца"
          - "кебаб 20 см." -> canonical_name="кебаб"
          - "кока кола 1 л" -> canonical_name="кола"

        Convert quantities to grams and output ONLY grams:
        - liters/ml: assume 1 ml = 1 g (so 1 l = 1000 g)
        - pieces (e.g., 4 мандаринки): estimate edible grams
        - bowls/portions/half pizza: estimate grams

        Return ONLY JSON matching the schema. No extra text.

        USER_TEXT:
        {user_text}
        """

        # noinspection PyTypeChecker
        response = self._client.responses.create(
            model=model,
            input=[
                {"role": "user", "content": [{"type": "input_text", "text": prompt}]}
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "text_to_items",
                    "strict": True,
                    "schema": ITEMS_SCHEMA,
                }
            },
        )
        return OpenAIProductListResponseDTO.model_validate(
            self._response_to_json(response)
        )

    def unknown_to_nutrition(
        self, raw_names: set[str], model: str
    ) -> OpenAIProductCreationListResponseDTO:
        joined = "\n".join([f"- {x}" for x in raw_names])

        prompt = f"""
            You are a nutrition assistant.
            For each raw_name, return a normalized Ukrainian product name (name_ua)
            and typical macros per 100g (kcal, protein, fat, carbs).
            New product name (name_ua) must be short and generic, removing any size, brand, flavor, or variant.
            If it is a drink, still return per 100g assuming 1 ml ≈ 1 g.
            Do not invent brands unless clearly indicated.
            Return ONLY JSON matching schema.
    
            RAW_NAMES:
            {joined}
        """

        # noinspection PyTypeChecker
        response = self._client.responses.create(
            model=model,
            input=[
                {"role": "user", "content": [{"type": "input_text", "text": prompt}]}
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "unknown_to_nutrition",
                    "strict": True,
                    "schema": UNKNOWN_TO_NUTRITION_SCHEMA,
                }
            },
        )
        return OpenAIProductCreationListResponseDTO.model_validate(
            self._response_to_json(response)
        )

    @staticmethod
    def _response_to_json(response) -> dict[str, Any]:
        if hasattr(response, "output_text") and response.output_text:
            return json.loads(response.output_text)

        out = response.output[0].content[0]
        txt = getattr(out, "text", None) or getattr(out, "content", None)
        if isinstance(txt, str):
            return json.loads(txt)

        raise RuntimeError("Cannot parse OpenAI response JSON")
