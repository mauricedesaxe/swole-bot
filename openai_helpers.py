import time
from datetime import datetime, timedelta
import backoff
import openai
import os
import threading

class RateLimiter:
    """
    A simple rate limiter to prevent exceeding the token limit of an API.
    """

    def __init__(self, tokens_per_min):
        """
        Initialize the rate limiter with the number of tokens allowed per minute.
        """
        self.tokens_per_min = tokens_per_min
        self.tokens_used = 0
        self.last_reset = datetime.now()
        
    def wait_if_needed(self, tokens_requested):
        """
        Wait if needed to prevent exceeding the token limit.
        """
        current_time = datetime.now()
        
        # Reset counter if a minute has passed
        if current_time - self.last_reset >= timedelta(minutes=1):
            self.tokens_used = 0
            self.last_reset = current_time
            
        # Check if we would exceed the limit
        if self.tokens_used + tokens_requested > self.tokens_per_min:
            # Calculate wait time needed
            wait_time = 60 - (current_time - self.last_reset).total_seconds()
            if wait_time > 0:
                time.sleep(wait_time)
                self.tokens_used = 0
                self.last_reset = datetime.now()
        
        self.tokens_used += tokens_requested 


rate_limiter = RateLimiter(tokens_per_min=190_000)  # Setting slightly below the 200k limit
mutex = threading.Lock()  # Mutex for synchronizing OpenAI calls

@backoff.on_exception(
    backoff.expo,
    openai.RateLimitError,
    max_tries=5,
    max_time=30
)
def make_openai_call(messages, model="gpt-4o-mini", max_tokens=150, temperature=0.0):
    """Make an OpenAI API call with rate limiting and retries."""
    # Estimate tokens (rough estimate)
    estimated_tokens = sum(len(m["content"].split()) * 1.3 for m in messages) + max_tokens
    
    rate_limiter.wait_if_needed(estimated_tokens)
    
    with mutex:  # Ensure only one call is made at a time
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response
        except openai.RateLimitError as e:
            if "Rate limit" in str(e): 
                print(f"Rate limit exceeded: {e}. Retrying after waiting.")
                time.sleep(1)  
            raise  
