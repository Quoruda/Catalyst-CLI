import json
from discovery import nesting_level, current_step_callback, available_agents

schema = {
    "name": "delegate_to_adaptive_worker",
    "description": (
        "Delegates a complex or isolated sub-task to a fresh, adaptive sub-worker agent. "
        "The worker will dynamically route the request and select the optimal skills. "
        "Use this to run complex tasks in parallel or in isolation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The exact sub-task description, highly detailed and self-contained with all context."
            },
            "directives": {
                "type": "string",
                "description": "Optional custom guidelines or persona requirements for the worker (e.g. 'Act as a strict code reviewer')."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

def delegate_to_adaptive_worker(query: str, directives: str = "") -> str:
    """Delegates a task to the metamorph agent acting as an adaptive worker."""
    metamorph_agent = available_agents.get("metamorph")
    if not metamorph_agent:
        return "Error: metamorph agent is not available."

    current_level = nesting_level.get()
    
    # We could theoretically protect against infinite recursion here
    if current_level > 5:
        return "Error: Maximum delegation depth exceeded."
        
    cb = current_step_callback.get()
    token = nesting_level.set(current_level + 1)
    
    try:
        # Prepend directives to the query if provided, so the worker adopts the persona
        if directives:
            query = f"[PERSONA DIRECTIVE: {directives}]\n\n{query}"
            
        result = metamorph_agent.run(query, history=[], step_callback=cb)
        return result
    except Exception as e:
        return f"Worker execution failed: {str(e)}"
    finally:
        nesting_level.reset(token)
