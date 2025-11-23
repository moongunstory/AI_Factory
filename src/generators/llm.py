"""LLM generator using llama.cpp."""
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any

from ..common.config import Config
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class LlamaClient:
    """Client for interacting with llama.cpp."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        temperature: float = Config.LLM_TEMPERATURE,
        max_tokens: int = Config.LLM_MAX_TOKENS,
        top_p: float = Config.LLM_TOP_P,
        threads: int = Config.LLM_THREADS,
    ):
        """Initialize the Llama client.

        Args:
            model_path: Path to the GGUF model file
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            threads: Number of threads to use
        """
        self.model_path = model_path or Config.get_model_file()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.threads = threads

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        if not Config.LLAMA_CPP_PATH.exists():
            raise FileNotFoundError(f"llama-cli not found: {Config.LLAMA_CPP_PATH}")

        logger.info(f"Initialized LlamaClient with model: {self.model_path.name}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text using llama.cpp.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text
        """
        # Build the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Build llama.cpp command
        cmd = [
            str(Config.LLAMA_CPP_PATH),
            "-m", str(self.model_path),
            "-p", full_prompt,
            "-n", str(max_tokens or self.max_tokens),
            "--temp", str(temperature or self.temperature),
            "--top-p", str(self.top_p),
            "-t", str(self.threads),
            "--log-disable",  # Disable internal logging
        ]

        logger.info(f"Running llama.cpp with prompt length: {len(full_prompt)} chars")
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            output = result.stdout.strip()
            logger.info(f"Generated {len(output)} characters")
            return output

        except subprocess.CalledProcessError as e:
            logger.error(f"llama.cpp failed: {e.stderr}")
            raise RuntimeError(f"LLM generation failed: {e.stderr}")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate JSON output using llama.cpp.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional arguments for generate()

        Returns:
            Parsed JSON dictionary
        """
        # Enhance system prompt to enforce JSON output
        json_system_prompt = (
            system_prompt or ""
        ) + "\n\nYou must respond with valid JSON only. No additional text."

        output = self.generate(prompt, system_prompt=json_system_prompt, **kwargs)

        # Try to extract JSON from the output
        try:
            # Find JSON content (between first { and last })
            start_idx = output.find('{')
            end_idx = output.rfind('}')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON object found in output")

            json_str = output[start_idx:end_idx + 1]
            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw output: {output}")
            raise RuntimeError(f"Failed to parse JSON from LLM output: {e}")
