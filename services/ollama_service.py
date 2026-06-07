import json
import requests
import re
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self, api_url="http://localhost:11434", model="mistral"):
        self.api_url = api_url.rstrip('/')
        self.model = model

    def check_connection(self):
        """
        Checks if Ollama is reachable and the model is loaded.
        """
        try:
            # First check if Ollama service is running
            response = requests.get(f"{self.api_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = [m.get("name") for m in response.json().get("models", [])]
                # Check if configured model exists (allowing model name variants e.g. mistral:latest)
                model_exists = any(self.model in m for m in models)
                if not model_exists:
                    logger.warning(f"Ollama is running, but model '{self.model}' was not found in: {models}")
                return response.status_code == 200
            return False
        except Exception:
            return False

    def query_agent(self, system_prompt, user_prompt):
        """
        Queries Ollama model with system and user prompts.
        Forces JSON output format and attempts to parse it.
        """
        if not self.check_connection():
            logger.error(f"Ollama not running or unreachable at {self.api_url} with model {self.model}.")
            raise ConnectionError(f"Ollama is unreachable or model '{self.model}' is not loaded.")

        url = f"{self.api_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=45)
            if response.status_code != 200:
                logger.error(f"Ollama returned error status {response.status_code}: {response.text}")
                raise RuntimeError(f"Ollama API error: {response.text}")

            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            return self._parse_json_response(message_content)

        except Exception as e:
            logger.error(f"Failed to query Ollama API: {str(e)}")
            raise e

    def _parse_json_response(self, text):
        """
        Robustly extracts and parses JSON content from LLM response text,
        handling possible markdown block formatting wrapper.
        """
        cleaned = text.strip()
        # Remove markdown code fence wrapper if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Ollama response. Raw: {text}. Error: {e}")
            # Try to pull out something using regex as a last resort
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            raise ValueError("Ollama response could not be parsed as JSON")
