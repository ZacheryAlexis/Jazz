import ollama
import requests
import time


class OllamaEmbedder:
    """Class to get embeddings using the Ollama API."""
    
    def __init__(self, model_name: str = "nomic-embed-text:v1.5", timeout: int = 60, max_retries: int = 5) -> None:
        self.model_name = model_name
        self.timeout = timeout  # 60 second timeout per embedding call
        self.max_retries = max_retries  # 5 attempts with longer backoff
        # Create client with explicit timeout
        self.client = ollama.Client(timeout=timeout)
    
    @staticmethod
    def _sanitize_input(text: str) -> str:
        """Sanitize input text to prevent Ollama crashes."""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove null bytes
        text = text.replace('\x00', ' ')
        
        # Remove most control characters except newlines/tabs
        text = ''.join(
            c if ord(c) >= 32 or c in '\n\r\t' else ' '
            for c in text
        )
        
        # Normalize whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Limit to reasonable length (8000 chars = ~2000 tokens)
        text = text[:8000].strip()
        
        return text
    
    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:
        """
        Get embeddings for a list of sentences using the Ollama API with retry logic.

        Args:
            sentences (list[str] | str): List of sentences to embed.

        Returns:
            list[list[float]]: List of embeddings for each sentence.
        """
        # Sanitize inputs
        if isinstance(sentences, str):
            sentences = [self._sanitize_input(sentences)]
        else:
            sentences = [self._sanitize_input(s) for s in sentences]
        
        # Filter out empty strings
        sentences = [s for s in sentences if s]
        if not sentences:
            raise ValueError("No non-empty content to embed after sanitization")
        
        # Embed one sentence at a time to prevent Ollama from crashing
        embeddings = []
        for i, sentence in enumerate(sentences, 1):
            for attempt in range(self.max_retries):
                try:
                    response = self.client.embed(model=self.model_name, input=sentence)
                    embeddings.append(response.embeddings[0])
                    # Small delay between requests to let Ollama clean up resources
                    # Increase delay to prevent resource exhaustion on Windows
                    if i % 5 == 0:  # Every 5 requests (more frequent than before)
                        time.sleep(0.2)  # Increased from 0.1s
                    break  # Success, move to next sentence
                except requests.exceptions.Timeout as e:
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
                    else:
                        raise TimeoutError(f"Ollama embedding request timed out after {self.max_retries} attempts")
                except (requests.exceptions.ConnectionError, ConnectionError) as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s, 40s, 50s backoff - give Ollama time to restart
                        time.sleep(wait_time)
                    else:
                        raise RuntimeError(f"Ollama connection failed after {self.max_retries} attempts: {e}")
                except Exception as e:
                    # Catch ResponseError and other exceptions from Ollama crashes
                    # and retry with backoff
                    if attempt < self.max_retries - 1:
                        wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s, 40s, 50s backoff - give Ollama time to restart
                        time.sleep(wait_time)
                    else:
                        raise RuntimeError(f"Failed to get embeddings from Ollama after {self.max_retries} attempts: {e}")
        
        return embeddings

