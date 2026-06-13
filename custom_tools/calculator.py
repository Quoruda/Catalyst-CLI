def calculator(expression: str) -> str:
    try:
        allowed_chars = "0123456789+-*/(). "
        if all(c in allowed_chars for c in expression):
            return str(eval(expression))
        return "Error: Invalid characters in expression."
    except Exception as e:
        return f"Error: {str(e)}"

schema = {
    "name": "calculator",
    "description": "Calculates the result of a simple mathematical expression.",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The math expression to evaluate."
            }
        },
        "required": ["expression"]
    }
}
