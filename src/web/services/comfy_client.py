"""ComfyUI HTTP client for SDXL image generation.

This module provides a Python client for ComfyUI's HTTP API,
specifically configured for generating vertical images (1080x1920)
using SDXL Base + Refiner.
"""
import json
import time
import uuid
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from io import BytesIO
from PIL import Image

from src.common.logger import setup_logger

logger = setup_logger(__name__)


class ComfyUIClient:
    """Client for ComfyUI HTTP API (SDXL txt2img + refiner)."""

    def __init__(
        self,
        server_url: str = "http://127.0.0.1:8188",
        model_base: str = "sdxl_base_1.0.safetensors",
        model_refiner: str = "sdxl_refiner_1.0.safetensors",
    ):
        """Initialize ComfyUI client.

        Args:
            server_url: ComfyUI server URL
            model_base: SDXL base model filename
            model_refiner: SDXL refiner model filename
        """
        self.server_url = server_url.rstrip("/")
        self.model_base = model_base
        self.model_refiner = model_refiner

        logger.info(f"ComfyUIClient initialized: {self.server_url}")
        logger.info(f"  Base model: {model_base}")
        logger.info(f"  Refiner model: {model_refiner}")

    def generate_vertical_image(
        self,
        prompt: str,
        out_path: Path,
        seed: Optional[int] = None,
        steps_base: int = 25,
        steps_refiner: int = 15,
        cfg: float = 7.0,
        sampler: str = "euler_ancestral",
        scheduler: str = "normal",
        denoise: float = 1.0,
    ) -> Dict[str, Any]:
        """Generate a vertical 1080x1920 image using SDXL Base + Refiner.

        Args:
            prompt: Text prompt for image generation
            out_path: Output file path (PNG)
            seed: Random seed (auto-generated if None)
            steps_base: Sampling steps for base model
            steps_refiner: Sampling steps for refiner
            cfg: CFG scale (classifier-free guidance)
            sampler: Sampler name (euler, euler_ancestral, etc.)
            scheduler: Scheduler type (normal, karras, etc.)
            denoise: Denoise strength (0.0-1.0)

        Returns:
            Metadata dictionary with seed, cfg, steps, etc.
        """
        if seed is None:
            seed = int(time.time() * 1000) % (2**32)

        logger.info(f"Generating vertical image: {out_path.name}")
        logger.info(f"  Prompt: {prompt[:80]}...")
        logger.info(f"  Seed: {seed}, Steps: {steps_base}+{steps_refiner}, CFG: {cfg}")

        # Build the workflow JSON
        workflow = self._build_sdxl_workflow(
            prompt=prompt,
            seed=seed,
            steps_base=steps_base,
            steps_refiner=steps_refiner,
            cfg=cfg,
            sampler=sampler,
            scheduler=scheduler,
            denoise=denoise,
        )

        # Submit the workflow
        prompt_id = self._queue_prompt(workflow)
        logger.info(f"Queued prompt: {prompt_id}")

        # Wait for completion
        success = self._wait_for_completion(prompt_id, timeout=300)
        if not success:
            raise RuntimeError(f"Image generation timed out for prompt {prompt_id}")

        # Download the image
        image_data = self._get_image(prompt_id)

        # Save to file
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(image_data)

        logger.info(f"✓ Image saved: {out_path}")

        # Return metadata
        metadata = {
            "prompt": prompt,
            "seed": seed,
            "steps_base": steps_base,
            "steps_refiner": steps_refiner,
            "cfg": cfg,
            "sampler": sampler,
            "scheduler": scheduler,
            "denoise": denoise,
            "width": 1080,
            "height": 1920,
            "model_base": self.model_base,
            "model_refiner": self.model_refiner,
        }

        # Save metadata JSON
        metadata_path = out_path.with_suffix(".json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata

    def _build_sdxl_workflow(
        self,
        prompt: str,
        seed: int,
        steps_base: int,
        steps_refiner: int,
        cfg: float,
        sampler: str,
        scheduler: str,
        denoise: float,
    ) -> Dict[str, Any]:
        """Build a ComfyUI workflow for SDXL Base + Refiner (vertical 1080x1920).

        This creates a standard SDXL workflow with:
        - CLIP text encoding (positive prompt)
        - Empty negative prompt
        - KSampler for base model
        - VAE decode
        - Refiner upscaling pass
        - Final VAE decode and save

        Returns:
            ComfyUI workflow dictionary
        """
        workflow = {
            # Load SDXL base checkpoint
            "1": {
                "inputs": {
                    "ckpt_name": self.model_base
                },
                "class_type": "CheckpointLoaderSimple"
            },
            # Load SDXL refiner checkpoint
            "2": {
                "inputs": {
                    "ckpt_name": self.model_refiner
                },
                "class_type": "CheckpointLoaderSimple"
            },
            # Positive prompt (CLIP text encode for base)
            "3": {
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            # Negative prompt (empty for base)
            "4": {
                "inputs": {
                    "text": "blurry, low quality, distorted, watermark, text, logo",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            # Empty latent image (1080x1920 vertical)
            "5": {
                "inputs": {
                    "width": 1080,
                    "height": 1920,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            # KSampler (base model)
            "6": {
                "inputs": {
                    "seed": seed,
                    "steps": steps_base,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": denoise,
                    "model": ["1", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            # VAE decode (base output)
            "7": {
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["1", 2]
                },
                "class_type": "VAEDecode"
            },
            # Encode back to latent for refiner
            "8": {
                "inputs": {
                    "pixels": ["7", 0],
                    "vae": ["2", 2]
                },
                "class_type": "VAEEncode"
            },
            # CLIP text encode for refiner (positive)
            "9": {
                "inputs": {
                    "text": prompt,
                    "clip": ["2", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            # CLIP text encode for refiner (negative)
            "10": {
                "inputs": {
                    "text": "blurry, low quality, distorted",
                    "clip": ["2", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            # KSampler (refiner)
            "11": {
                "inputs": {
                    "seed": seed,
                    "steps": steps_refiner,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": 0.3,  # Lower denoise for refiner
                    "model": ["2", 0],
                    "positive": ["9", 0],
                    "negative": ["10", 0],
                    "latent_image": ["8", 0]
                },
                "class_type": "KSampler"
            },
            # Final VAE decode
            "12": {
                "inputs": {
                    "samples": ["11", 0],
                    "vae": ["2", 2]
                },
                "class_type": "VAEDecode"
            },
            # Save image
            "13": {
                "inputs": {
                    "filename_prefix": "ai_short_factory",
                    "images": ["12", 0]
                },
                "class_type": "SaveImage"
            }
        }

        return workflow

    def _queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue a prompt/workflow on ComfyUI server.

        Args:
            workflow: ComfyUI workflow dictionary

        Returns:
            Prompt ID (UUID)
        """
        prompt_id = str(uuid.uuid4())
        payload = {
            "prompt": workflow,
            "client_id": prompt_id
        }

        response = requests.post(
            f"{self.server_url}/prompt",
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        return result.get("prompt_id", prompt_id)

    def _wait_for_completion(self, prompt_id: str, timeout: int = 300) -> bool:
        """Wait for a prompt to complete.

        Args:
            prompt_id: The prompt ID to wait for
            timeout: Maximum wait time in seconds

        Returns:
            True if completed successfully, False if timed out
        """
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.error(f"Timeout waiting for prompt {prompt_id}")
                return False

            try:
                response = requests.get(
                    f"{self.server_url}/history/{prompt_id}",
                    timeout=10
                )
                response.raise_for_status()
                history = response.json()

                if prompt_id in history:
                    status = history[prompt_id].get("status", {})
                    if status.get("completed", False):
                        logger.info(f"Prompt {prompt_id} completed")
                        return True

            except Exception as e:
                logger.warning(f"Error checking status: {e}")

            time.sleep(2)

    def _get_image(self, prompt_id: str) -> bytes:
        """Retrieve the generated image data.

        Args:
            prompt_id: The prompt ID

        Returns:
            Image data as bytes
        """
        # Get history to find the output image
        response = requests.get(
            f"{self.server_url}/history/{prompt_id}",
            timeout=10
        )
        response.raise_for_status()
        history = response.json()

        if prompt_id not in history:
            raise RuntimeError(f"Prompt {prompt_id} not found in history")

        outputs = history[prompt_id].get("outputs", {})

        # Find the SaveImage node output
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                images = node_output["images"]
                if images:
                    # Get the first image
                    img_info = images[0]
                    filename = img_info["filename"]
                    subfolder = img_info.get("subfolder", "")
                    folder_type = img_info.get("type", "output")

                    # Download the image
                    params = {
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": folder_type
                    }
                    img_response = requests.get(
                        f"{self.server_url}/view",
                        params=params,
                        timeout=30
                    )
                    img_response.raise_for_status()
                    return img_response.content

        raise RuntimeError(f"No image found for prompt {prompt_id}")

    def is_healthy(self) -> bool:
        """Check if ComfyUI server is healthy.

        Returns:
            True if server is responsive, False otherwise
        """
        try:
            response = requests.get(f"{self.server_url}/system_stats", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_server_info(self) -> Dict[str, Any]:
        """Get ComfyUI server information.

        Returns:
            Server info dictionary
        """
        try:
            response = requests.get(f"{self.server_url}/system_stats", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            return {}
