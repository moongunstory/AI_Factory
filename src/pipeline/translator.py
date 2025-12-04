"""Translation module - bidirectional translation between Korean and English using NLLB."""
from typing import Optional, Literal
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from ..common.config import Config
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class Translator:
    """Translate text between Korean and English using NLLB-200."""

    def __init__(self, model_path: Optional[Path] = None):
        """Initialize the translator with NLLB model.

        Args:
            model_path: Optional path to NLLB model. If None, uses Config.TRANSLATION_MODEL_PATH.
        """
        self.model_path = model_path or Config.TRANSLATION_MODEL_PATH
        self.model = None
        self.tokenizer = None
        self._load_model()
        logger.info("Translator initialized with NLLB-200 model")

    def _load_model(self):
        """Load NLLB model and tokenizer."""
        try:
            logger.info(f"Loading NLLB model from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )

            # Move to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("NLLB model loaded on GPU")
            else:
                logger.info("NLLB model loaded on CPU")

        except Exception as e:
            logger.error(f"Failed to load NLLB model: {e}")
            raise

    def translate(
        self,
        text: str,
        source_lang: Literal["ko", "en"] = "en",
        target_lang: Literal["ko", "en"] = "ko",
        max_length: int = 512
    ) -> str:
        """Translate text between Korean and English.

        Args:
            text: Text to translate
            source_lang: Source language code ("ko" or "en")
            target_lang: Target language code ("ko" or "en")
            max_length: Maximum length of generated translation

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return ""

        # Map language codes to NLLB format
        lang_map = {
            "ko": "kor_Hang",
            "en": "eng_Latn"
        }

        src_lang = lang_map.get(source_lang, "eng_Latn")
        tgt_lang = lang_map.get(target_lang, "kor_Hang")

        try:
            # Tokenize
            self.tokenizer.src_lang = src_lang
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length
            )

            # Move to same device as model
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Generate translation
            translated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.lang_code_to_id[tgt_lang],
                max_length=max_length,
                num_beams=5,
                early_stopping=True
            )

            # Decode
            translated_text = self.tokenizer.batch_decode(
                translated_tokens,
                skip_special_tokens=True
            )[0]

            logger.debug(f"Translated ({source_lang}→{target_lang}): {text[:50]}... → {translated_text[:50]}...")
            return translated_text.strip()

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise

    def korean_to_english(self, korean_text: str) -> str:
        """Translate Korean text to English.

        Args:
            korean_text: Korean text to translate

        Returns:
            English translation
        """
        return self.translate(korean_text, source_lang="ko", target_lang="en")

    def english_to_korean(self, english_text: str) -> str:
        """Translate English text to Korean.

        Args:
            english_text: English text to translate

        Returns:
            Korean translation
        """
        return self.translate(english_text, source_lang="en", target_lang="ko")


def translate_text(
    text: str,
    source_lang: Literal["ko", "en"] = "en",
    target_lang: Literal["ko", "en"] = "ko"
) -> str:
    """Convenience function to translate text.

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Translated text
    """
    translator = Translator()
    return translator.translate(text, source_lang, target_lang)
