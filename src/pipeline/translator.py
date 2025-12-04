"""Translation module - bidirectional translation between Korean and English using NLLB.

- Uses NLLB-200 distilled model (Seq2Seq) for KO <-> EN translation
- Loads model once per process and reuses it (singleton)
- Automatically uses GPU (CUDA) with float16 when available
"""

from typing import Optional, Literal
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from ..common.config import Config
from ..common.logger import setup_logger

logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# Singleton translator instance (모델을 매 호출마다 다시 로딩하지 않도록)
# ---------------------------------------------------------------------------

_TRANSLATOR_SINGLETON = None  # type: Optional["Translator"]


def get_translator() -> "Translator":
    """Get a shared Translator instance (lazy singleton)."""
    global _TRANSLATOR_SINGLETON
    if _TRANSLATOR_SINGLETON is None:
        _TRANSLATOR_SINGLETON = Translator()
    return _TRANSLATOR_SINGLETON


class Translator:
    """Translate text between Korean and English using NLLB-200."""

    def __init__(self, model_path: Optional[Path] = None) -> None:
        """Initialize the translator with NLLB model.

        Args:
            model_path: Optional path to NLLB model.
                        If None, uses Config.TRANSLATION_MODEL_PATH.
        """
        self.model_path: Path = model_path or Config.TRANSLATION_MODEL_PATH
        self.model: Optional[torch.nn.Module] = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._load_model()
        logger.info(
            "Translator initialized with NLLB-200 model on %s", self.device.type
        )

    # ------------------------------------------------------------------ #
    # Model loading                                                      #
    # ------------------------------------------------------------------ #

    def _load_model(self) -> None:
        """Load NLLB model and tokenizer from local path."""
        try:
            logger.info(f"Loading NLLB model from {self.model_path}")

            # Tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True,
            )

            # Model (float16 on GPU, float32 on CPU)
            model_kwargs = {
                "local_files_only": True,
            }
            if self.device.type == "cuda":
                model_kwargs["torch_dtype"] = torch.float16

            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                str(self.model_path),
                **model_kwargs,
            )

            self.model.to(self.device)
            self.model.eval()

            logger.info("NLLB model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load NLLB model: {e}")
            raise

    # ------------------------------------------------------------------ #
    # Core translation                                                   #
    # ------------------------------------------------------------------ #

    def translate(
        self,
        text: str,
        source_lang: Literal["ko", "en"] = "en",
        target_lang: Literal["ko", "en"] = "ko",
        max_length: int = 512,
    ) -> str:
        """Translate text between Korean and English.

        Args:
            text: Text to translate.
            source_lang: Source language code ("ko" or "en").
            target_lang: Target language code ("ko" or "en").
            max_length: Maximum length of generated translation.

        Returns:
            Translated text (string). Empty string if input is empty.
        """
        if not text or not text.strip():
            return ""

        # Map project language codes -> NLLB internal language codes
        # NOTE: distilled-600M 경량 버전은 lang_code_to_id가 없을 수 있으므로
        #       여기서는 src_lang만 설정하고 forced_bos_token_id는 사용하지 않는다.
        lang_map = {
            "ko": "kor_Hang",
            "en": "eng_Latn",
        }

        src_lang = lang_map.get(source_lang, "eng_Latn")
        tgt_lang = lang_map.get(target_lang, "kor_Hang")

        try:
            # Set source language for tokenizer (NLLB style)
            # 일부 NLLB 토크나이저는 src_lang 필드를 사용함
            if hasattr(self.tokenizer, "src_lang"):
                self.tokenizer.src_lang = src_lang

            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Optional: try to get forced_bos_token_id when available
            # (경량 버전은 lang_code_to_id가 없으므로 hasattr 체크로 안전하게 처리)
            generate_kwargs = {
                "max_length": max_length,
                "num_beams": 2,            # quality/speed balance
                "no_repeat_ngram_size": 3, # prevent repetition
                "early_stopping": True,
            }

            if hasattr(self.tokenizer, "lang_code_to_id"):
                try:
                    forced_bos = self.tokenizer.lang_code_to_id[tgt_lang]
                    generate_kwargs["forced_bos_token_id"] = forced_bos
                except Exception as e:
                    # 키 없거나 기타 문제면 그냥 경고만 띄우고 강제 BOS 없이 진행
                    logger.warning(
                        f"Failed to resolve lang_code_to_id for {tgt_lang}: {e}"
                    )

            # Generate translation (no_grad: inference only)
            with torch.no_grad():
                translated_tokens = self.model.generate(**inputs, **generate_kwargs)

            # Decode first sequence
            translated_text = self.tokenizer.batch_decode(
                translated_tokens,
                skip_special_tokens=True,
            )[0]

            logger.debug(
                "Translated (%s→%s): %s... → %s...",
                source_lang,
                target_lang,
                text[:50],
                translated_text[:50],
            )
            return translated_text.strip()

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # 번역 실패 시, 전체 파이프라인이 죽지 않도록
            # 원문을 그대로 반환하는 전략도 가능하다.
            # 여기서는 일단 예외를 다시 던져서 상위에서 처리하게 둔다.
            raise

    # ------------------------------------------------------------------ #
    # Convenience wrappers                                               #
    # ------------------------------------------------------------------ #

    def korean_to_english(self, korean_text: str) -> str:
        """Translate Korean text to English."""
        return self.translate(korean_text, source_lang="ko", target_lang="en")

    def english_to_korean(self, english_text: str) -> str:
        """Translate English text to Korean."""
        return self.translate(english_text, source_lang="en", target_lang="ko")


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def translate_text(
    text: str,
    source_lang: Literal["ko", "en"] = "en",
    target_lang: Literal["ko", "en"] = "ko",
    max_length: int = 512,
) -> str:
    """Convenience function to translate text using shared Translator instance.

    Args:
        text: Text to translate.
        source_lang: Source language code ("ko" or "en").
        target_lang: Target language code ("ko" or "en").
        max_length: Maximum length of generated translation.

    Returns:
        Translated text.
    """
    translator = get_translator()
    return translator.translate(text, source_lang=source_lang, target_lang=target_lang, max_length=max_length)
