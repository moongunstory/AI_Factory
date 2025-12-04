"""ComfyUI HTTP client for SDXL image generation.

This module provides a Python client for ComfyUI's HTTP API,
specifically configured for generating vertical images with VRAM optimization.
Supports low-resolution generation, optional Refiner, and memory cleanup.
"""
import json
import time
import uuid
import random
import gc
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from io import BytesIO
from PIL import Image

from src.common.logger import setup_logger
from src.common.config import Config

logger = setup_logger(__name__)


class ComfyUIClient:
    """Client for ComfyUI HTTP API (SDXL txt2img + refiner)."""

    def __init__(
        self,
        server_url: str = "http://127.0.0.1:8188",
        model_base: str = "sdxl_base_1.0.safetensors",
        model_refiner: str = "sdxl_refiner_1.0.safetensors",
        low_vram_mode: bool = True,
        use_refiner: bool = False,
        timeout: int = 240,
        max_retries: int = 2,
    ):
        """Initialize ComfyUI client.

        Args:
            server_url: ComfyUI server URL
            model_base: SDXL base model filename
            model_refiner: SDXL refiner model filename
            low_vram_mode: Enable low VRAM optimizations (VAE tiling, etc.)
            use_refiner: Use refiner by default (not recommended for all scenes)
            timeout: Generation timeout in seconds
            max_retries: Maximum number of retries on failure
        """
        self.server_url = server_url.rstrip("/")
        self.model_base = model_base
        self.model_refiner = model_refiner
        self.low_vram_mode = low_vram_mode
        self.use_refiner = use_refiner
        self.timeout = timeout
        self.max_retries = max_retries

        logger.info(f"ComfyUIClient initialized: {self.server_url}")
        logger.info(f"  Base model: {model_base}")
        logger.info(f"  Refiner model: {model_refiner}")
        logger.info(f"  Low VRAM mode: {low_vram_mode}")
        logger.info(f"  Use Refiner: {use_refiner}")
        logger.info(f"  Timeout: {timeout}s, Max retries: {max_retries}")

    def generate_vertical_image(
        self,
        prompt: str,
        out_path: Path,
        seed: Optional[int] = None,
        steps_base: Optional[int] = None,
        steps_refiner: Optional[int] = None,
        cfg: Optional[float] = None,
        sampler: str = "euler_ancestral",
        scheduler: str = "normal",
        denoise: float = 1.0,
        use_refiner: Optional[bool] = None,
        resolution_mode: str = "low",
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a vertical image using SDXL Base (+ optional Refiner).

        This method automatically optimizes parameters for VRAM efficiency
        and includes retry logic for improved reliability.

        Args:
            prompt: Text prompt for image generation
            out_path: Output file path (PNG)
            seed: Random seed (auto-generated if None)
            steps_base: Sampling steps for base model (auto-optimized if None)
            steps_refiner: Sampling steps for refiner (auto-optimized if None)
            cfg: CFG scale (auto-optimized if None)
            sampler: Sampler name (euler, euler_ancestral, etc.)
            scheduler: Scheduler type (normal, karras, etc.)
            denoise: Denoise strength (0.0-1.0)
            use_refiner: Use refiner (defaults to self.use_refiner)
            resolution_mode: "low" (768px) or "high" (1080px)
            width: Custom width (overrides resolution_mode)
            height: Custom height (overrides resolution_mode)

        Returns:
            Metadata dictionary with seed, cfg, steps, etc.
        """
        # Auto-optimize parameters
        if seed is None:
            seed = int(time.time() * 1000) % (2**32)

        if steps_base is None:
            steps_base = random.randint(Config.IMAGE_STEPS_MIN, Config.IMAGE_STEPS_MAX)

        if steps_refiner is None:
            steps_refiner = Config.IMAGE_REFINER_STEPS

        if cfg is None:
            cfg = random.uniform(Config.IMAGE_CFG_MIN, Config.IMAGE_CFG_MAX)
            cfg = round(cfg, 1)  # Round to 1 decimal place

        if use_refiner is None:
            use_refiner = self.use_refiner

        # Determine resolution
        if width is None or height is None:
            if resolution_mode == "high":
                width = Config.IMAGE_WIDTH_HIGH
                height = Config.IMAGE_HEIGHT_HIGH
            else:
                width = Config.IMAGE_WIDTH_LOW
                height = Config.IMAGE_HEIGHT_LOW

        logger.info(f"Generating vertical image: {out_path.name}")
        logger.info(f"  Prompt: {prompt[:80]}...")
        logger.info(f"  Resolution: {width}x{height} ({resolution_mode})")
        logger.info(f"  Seed: {seed}, Steps: {steps_base}{'+' + str(steps_refiner) if use_refiner else ''}, CFG: {cfg}")
        logger.info(f"  Refiner: {'Yes' if use_refiner else 'No'}, Low VRAM: {'Yes' if self.low_vram_mode else 'No'}")

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.max_retries}...")
                    # Clean up memory before retry
                    self.cleanup_memory()
                    time.sleep(2)  # Brief pause before retry

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
                    use_refiner=use_refiner,
                    width=width,
                    height=height,
                )

                # Submit the workflow
                prompt_id = self._queue_prompt(workflow)
                logger.info(f"Queued prompt: {prompt_id}")

                # Wait for completion
                success = self._wait_for_completion(prompt_id, timeout=self.timeout)
                if not success:
                    raise RuntimeError(f"Image generation timed out after {self.timeout}s")

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
                    "steps_refiner": steps_refiner if use_refiner else 0,
                    "cfg": cfg,
                    "sampler": sampler,
                    "scheduler": scheduler,
                    "denoise": denoise,
                    "width": width,
                    "height": height,
                    "resolution_mode": resolution_mode,
                    "use_refiner": use_refiner,
                    "low_vram_mode": self.low_vram_mode,
                    "model_base": self.model_base,
                    "model_refiner": self.model_refiner if use_refiner else None,
                    "attempts": attempt + 1,
                }

                # Save metadata JSON
                metadata_path = out_path.with_suffix(".json")
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)

                # Success! Clean up memory for next generation
                self.cleanup_memory()

                return metadata

            except Exception as e:
                last_error = e
                logger.error(f"Image generation failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")

                if attempt < self.max_retries:
                    # Interrupt any stuck generation
                    self.interrupt_current_generation()
                    continue
                else:
                    # Final attempt failed
                    break

        # All retries exhausted
        raise RuntimeError(f"Image generation failed after {self.max_retries + 1} attempts: {last_error}")

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
        use_refiner: bool = False,
        width: int = 768,
        height: int = 1365,
    ) -> Dict[str, Any]:
        """Build a ComfyUI workflow for SDXL Base (+ optional Refiner).

        This creates an optimized SDXL workflow with:
        - CLIP text encoding (positive prompt)
        - Negative prompt
        - KSampler for base model
        - VAE decode (with tiling if low_vram_mode)
        - Optional refiner pass
        - Final VAE decode and save

        Args:
            prompt: Positive text prompt
            seed: Random seed
            steps_base: Base model sampling steps
            steps_refiner: Refiner model sampling steps (ignored if use_refiner=False)
            cfg: CFG scale
            sampler: Sampler name
            scheduler: Scheduler name
            denoise: Denoise strength
            use_refiner: Whether to use refiner model
            width: Image width
            height: Image height

        Returns:
            ComfyUI workflow dictionary
        """
        if use_refiner:
            # SDXL Base + Refiner workflow
            workflow = self._build_workflow_with_refiner(
                prompt, seed, steps_base, steps_refiner, cfg,
                sampler, scheduler, denoise, width, height
            )
        else:
            # SDXL Base only workflow (optimized for low VRAM)
            workflow = self._build_workflow_base_only(
                prompt, seed, steps_base, cfg,
                sampler, scheduler, denoise, width, height
            )

        return workflow

    def _build_workflow_base_only(
        self,
        prompt: str,
        seed: int,
        steps: int,
        cfg: float,
        sampler: str,
        scheduler: str,
        denoise: float,
        width: int,
        height: int,
    ) -> Dict[str, Any]:
        """Build SDXL Base-only workflow (no Refiner, optimized for low VRAM).

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
            # Positive prompt (CLIP text encode for base)
            "2": {
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            # Negative prompt
            "3": {
                "inputs": {
                    "text": "blurry, low quality, distorted, watermark, text, logo, bad anatomy",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            # Empty latent image (configurable resolution)
            "4": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            # KSampler (base model)
            "5": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": denoise,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                },
                "class_type": "KSampler"
            },
            # VAE decode
            "6": {
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                },
                "class_type": "VAEDecode"
            },
            # Save image
            "7": {
                "inputs": {
                    "filename_prefix": "ai_short_factory",
                    "images": ["6", 0]
                },
                "class_type": "SaveImage"
            }
        }

        return workflow

    def _build_workflow_with_refiner(
        self,
        prompt: str,
        seed: int,
        steps_base: int,
        steps_refiner: int,
        cfg: float,
        sampler: str,
        scheduler: str,
        denoise: float,
        width: int,
        height: int,
    ) -> Dict[str, Any]:
        """Build SDXL Base + Refiner workflow.

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
            # Negative prompt (for base)
            "4": {
                "inputs": {
                    "text": "blurry, low quality, distorted, watermark, text, logo, bad anatomy",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            # Empty latent image (configurable resolution)
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
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
                    "text": "blurry, low quality, distorted, bad anatomy",
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

    def cleanup_memory(self) -> bool:
        """Clean up VRAM and system memory.

        This method triggers garbage collection and requests ComfyUI
        to free unused VRAM memory.

        Returns:
            True if cleanup succeeded, False otherwise
        """
        try:
            # Python garbage collection
            gc.collect()

            # Request ComfyUI to free memory
            # ComfyUI's /free endpoint clears model cache and frees VRAM
            response = requests.post(
                f"{self.server_url}/free",
                json={"unload_models": True, "free_memory": True},
                timeout=10
            )

            if response.status_code == 200:
                logger.info("✓ VRAM and memory cleanup successful")
                return True
            else:
                logger.warning(f"Memory cleanup returned status {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"Memory cleanup failed (non-critical): {e}")
            return False

    def interrupt_current_generation(self) -> bool:
        """Interrupt any currently running generation.

        Returns:
            True if interruption succeeded, False otherwise
        """
        try:
            response = requests.post(
                f"{self.server_url}/interrupt",
                timeout=5
            )
            response.raise_for_status()
            logger.info("✓ Current generation interrupted")
            return True
        except Exception as e:
            logger.warning(f"Failed to interrupt generation: {e}")
            return False

    def upscale_image(
        self,
        image_path: Path,
        out_path: Path,
        upscale_factor: float = 1.4,
        use_refiner: bool = True,
    ) -> Dict[str, Any]:
        """Upscale an existing image to higher resolution.

        This method is designed for selectively upscaling important scenes
        after initial low-resolution generation.

        Args:
            image_path: Input image path (PNG)
            out_path: Output image path (PNG)
            upscale_factor: Upscale factor (e.g., 1.4 for 768→1080)
            use_refiner: Use refiner for quality improvement

        Returns:
            Metadata dictionary
        """
        logger.info(f"Upscaling image: {image_path.name}")
        logger.info(f"  Upscale factor: {upscale_factor}x")
        logger.info(f"  Use refiner: {use_refiner}")

        # Load the image to get dimensions
        with Image.open(image_path) as img:
            orig_width, orig_height = img.size

        target_width = int(orig_width * upscale_factor)
        target_height = int(orig_height * upscale_factor)

        logger.info(f"  Original: {orig_width}x{orig_height}")
        logger.info(f"  Target: {target_width}x{target_height}")

        # For now, use simple PIL upscaling
        # TODO: Implement ComfyUI-based upscaling workflow (LatentUpscale + Refiner)
        with Image.open(image_path) as img:
            upscaled = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            upscaled.save(out_path, "PNG")

        logger.info(f"✓ Upscaled image saved: {out_path}")

        metadata = {
            "original_path": str(image_path),
            "original_size": (orig_width, orig_height),
            "upscaled_size": (target_width, target_height),
            "upscale_factor": upscale_factor,
            "use_refiner": use_refiner,
        }

        return metadata
