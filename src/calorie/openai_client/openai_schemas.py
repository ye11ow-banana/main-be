ITEMS_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "user": {"type": "string", "enum": ["Mykhailo", "Anastasiia"]},
                    "raw_name": {"type": "string"},
                    "weight": {"type": "string"},
                },
                "required": ["user", "raw_name", "weight"],
                "additionalProperties": False,
            },
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
        "unparsed": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["items", "warnings", "unparsed"],
    "additionalProperties": False,
}

UNKNOWN_TO_NUTRITION_SCHEMA = {
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "raw_name": {"type": "string"},
                    "name_ua": {"type": "string"},
                    "per_100g": {
                        "type": "object",
                        "properties": {
                            "proteins": {"type": "number", "minimum": 0},
                            "fats": {"type": "number", "minimum": 0},
                            "carbs": {"type": "number", "minimum": 0},
                            "calories": {"type": "number", "minimum": 0},
                        },
                        "required": ["proteins", "fats", "carbs", "calories"],
                        "additionalProperties": False,
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "assumptions": {"type": "string"},
                },
                "required": [
                    "raw_name",
                    "name_ua",
                    "per_100g",
                    "confidence",
                    "assumptions",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["products"],
    "additionalProperties": False,
}
