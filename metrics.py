import threading

class TokenMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        
    def add(self, prompt: int, completion: int):
        with self._lock:
            self.total_prompt_tokens += prompt
            self.total_completion_tokens += completion
            
    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

global_metrics = TokenMetrics()
