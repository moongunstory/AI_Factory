"""
Language Validation Utility

한국어 순수성 검증 및 한자(중국어) 감지 유틸리티
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def contains_chinese(text: str) -> bool:
    """
    텍스트에 중국어 한자(汉字)가 포함되어 있는지 감지

    Args:
        text: 검증할 텍스트

    Returns:
        True if Chinese characters found, False otherwise
    """
    if not text:
        return False

    for char in text:
        code = ord(char)
        # CJK Unified Ideographs: U+4E00-U+9FFF (한자)
        # CJK Extension A: U+3400-U+4DBF
        # CJK Extension B-F: U+20000-U+2A6DF, U+2A700-U+2B73F, etc.
        if (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0x20000 <= code <= 0x2A6DF):
            return True

    return False


def contains_japanese(text: str) -> bool:
    """
    텍스트에 일본어(히라가나/가타카나)가 포함되어 있는지 감지

    Args:
        text: 검증할 텍스트

    Returns:
        True if Japanese characters found, False otherwise
    """
    if not text:
        return False

    for char in text:
        code = ord(char)
        # Hiragana: U+3040-U+309F
        # Katakana: U+30A0-U+30FF
        if 0x3040 <= code <= 0x30FF:
            return True

    return False


def is_pure_korean(text: str, allow_punctuation: bool = True, allow_numbers: bool = True, allow_english: bool = False) -> bool:
    """
    텍스트가 순수 한국어(한글)로만 구성되어 있는지 검증

    Args:
        text: 검증할 텍스트
        allow_punctuation: 구두점 허용 여부
        allow_numbers: 숫자 허용 여부
        allow_english: 영문 허용 여부 (기본: False, 한국어 필드는 순수 한글만)

    Returns:
        True if text is pure Korean, False otherwise
    """
    if not text:
        return True  # 빈 문자열은 허용

    # 허용 문자 집합 정의
    allowed_chars = set()

    if allow_punctuation:
        allowed_chars.update('.,!?;:\'"()[]{}~-…、。「」『』・')

    if allow_numbers:
        allowed_chars.update('0123456789')

    if allow_english:
        allowed_chars.update('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

    for char in text:
        code = ord(char)

        # 한글 음절 (완성형): U+AC00-U+D7A3 (가-힣)
        if 0xAC00 <= code <= 0xD7A3:
            continue

        # 한글 자모 (호환용): U+3130-U+318F (ㄱ-ㅎ, ㅏ-ㅣ)
        if 0x3130 <= code <= 0x318F:
            continue

        # 공백 문자
        if char.isspace():
            continue

        # 기타 허용 문자
        if char in allowed_chars:
            continue

        # 허용되지 않은 문자 발견
        return False

    return True


def analyze_language(text: str) -> Dict[str, any]:
    """
    텍스트의 언어 구성 비율 분석

    Args:
        text: 분석할 텍스트

    Returns:
        언어 통계 딕셔너리
    """
    if not text:
        return {
            "korean_chars": 0,
            "chinese_chars": 0,
            "japanese_chars": 0,
            "english_chars": 0,
            "number_chars": 0,
            "other_chars": 0,
            "total_chars": 0,
            "korean_percentage": 0.0,
            "chinese_percentage": 0.0,
            "is_pure_korean": True
        }

    korean_chars = 0
    chinese_chars = 0
    japanese_chars = 0
    english_chars = 0
    number_chars = 0
    other_chars = 0

    for char in text:
        code = ord(char)

        # 공백 제외
        if char.isspace():
            continue

        # 한글 (가-힣, ㄱ-ㅎ, ㅏ-ㅣ)
        if (0xAC00 <= code <= 0xD7A3 or 0x3130 <= code <= 0x318F):
            korean_chars += 1
        # 한자
        elif (0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF):
            chinese_chars += 1
        # 일본어
        elif 0x3040 <= code <= 0x30FF:
            japanese_chars += 1
        # 영문
        elif char.isalpha():
            english_chars += 1
        # 숫자
        elif char.isdigit():
            number_chars += 1
        # 기타
        else:
            other_chars += 1

    total_chars = korean_chars + chinese_chars + japanese_chars + english_chars + number_chars + other_chars

    return {
        "korean_chars": korean_chars,
        "chinese_chars": chinese_chars,
        "japanese_chars": japanese_chars,
        "english_chars": english_chars,
        "number_chars": number_chars,
        "other_chars": other_chars,
        "total_chars": total_chars,
        "korean_percentage": (korean_chars / total_chars * 100.0) if total_chars > 0 else 0.0,
        "chinese_percentage": (chinese_chars / total_chars * 100.0) if total_chars > 0 else 0.0,
        "is_pure_korean": chinese_chars == 0 and japanese_chars == 0
    }


def find_non_korean_chars(text: str, max_examples: int = 5) -> List[Tuple[str, int, str]]:
    """
    텍스트에서 한국어가 아닌 문자들을 찾아 반환

    Args:
        text: 검증할 텍스트
        max_examples: 반환할 최대 예시 개수

    Returns:
        (문자, 유니코드, 설명) 튜플 리스트
    """
    if not text:
        return []

    non_korean_chars = []

    for idx, char in enumerate(text):
        if len(non_korean_chars) >= max_examples:
            break

        code = ord(char)

        # 한글, 공백, 구두점은 스킵
        if (0xAC00 <= code <= 0xD7A3 or
            0x3130 <= code <= 0x318F or
            char.isspace() or
            char in '.,!?;:\'"()[]{}~-…、。「」『』・0123456789'):
            continue

        # 한자 감지
        if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
            non_korean_chars.append((char, code, "Chinese (한자)"))
        # 일본어 감지
        elif 0x3040 <= code <= 0x30FF:
            non_korean_chars.append((char, code, "Japanese (日本語)"))
        # 영문 감지
        elif char.isalpha():
            non_korean_chars.append((char, code, "English"))
        # 기타
        else:
            non_korean_chars.append((char, code, "Other"))

    return non_korean_chars


def validate_korean_fields(data: Dict, korean_field_names: List[str], strict: bool = True) -> Tuple[bool, List[str]]:
    """
    딕셔너리의 한국어 필드들을 검증

    Args:
        data: 검증할 데이터 딕셔너리
        korean_field_names: 한국어여야 하는 필드 이름 리스트
        strict: 엄격 모드 (True: 순수 한글만, False: 한자만 없으면 됨)

    Returns:
        (is_valid, error_messages) 튜플
    """
    errors = []

    for field_name in korean_field_names:
        if field_name not in data:
            continue

        field_value = data[field_name]

        # 리스트나 중첩 구조 처리
        if isinstance(field_value, list):
            for idx, item in enumerate(field_value):
                if isinstance(item, dict):
                    # 재귀 검증
                    is_valid, sub_errors = validate_korean_fields(item, korean_field_names, strict)
                    if not is_valid:
                        errors.extend([f"{field_name}[{idx}].{err}" for err in sub_errors])
                elif isinstance(item, str):
                    if not _validate_single_field(item, f"{field_name}[{idx}]", strict, errors):
                        pass  # 이미 errors에 추가됨
        elif isinstance(field_value, dict):
            # 재귀 검증
            is_valid, sub_errors = validate_korean_fields(field_value, korean_field_names, strict)
            if not is_valid:
                errors.extend([f"{field_name}.{err}" for err in sub_errors])
        elif isinstance(field_value, str):
            if not _validate_single_field(field_value, field_name, strict, errors):
                pass  # 이미 errors에 추가됨

    return (len(errors) == 0, errors)


def _validate_single_field(text: str, field_name: str, strict: bool, errors: List[str]) -> bool:
    """
    단일 필드 검증 (내부 헬퍼 함수)
    """
    if not text:
        return True  # 빈 문자열은 허용

    # 한자 검사 (최우선)
    if contains_chinese(text):
        non_korean = find_non_korean_chars(text, max_examples=3)
        examples = ", ".join([f"'{char}' (U+{code:04X}, {desc})" for char, code, desc in non_korean])
        errors.append(f"{field_name}: 한자(Chinese) 감지됨 - {examples}")
        return False

    # 일본어 검사
    if contains_japanese(text):
        non_korean = find_non_korean_chars(text, max_examples=3)
        examples = ", ".join([f"'{char}' (U+{code:04X}, {desc})" for char, code, desc in non_korean])
        errors.append(f"{field_name}: 일본어(Japanese) 감지됨 - {examples}")
        return False

    # 엄격 모드: 순수 한글만 허용
    if strict and not is_pure_korean(text, allow_punctuation=True, allow_numbers=True, allow_english=False):
        non_korean = find_non_korean_chars(text, max_examples=3)
        if non_korean:
            examples = ", ".join([f"'{char}' (U+{code:04X}, {desc})" for char, code, desc in non_korean])
            errors.append(f"{field_name}: 순수 한국어 아님 - {examples}")
            return False

    return True


def log_language_stats(text: str, field_name: str = "text") -> None:
    """
    텍스트의 언어 통계를 로그로 출력

    Args:
        text: 분석할 텍스트
        field_name: 필드 이름 (로그용)
    """
    stats = analyze_language(text)

    logger.info(
        f"[Language Stats] {field_name}: "
        f"Korean={stats['korean_percentage']:.1f}%, "
        f"Chinese={stats['chinese_chars']} chars, "
        f"Japanese={stats['japanese_chars']} chars, "
        f"Pure Korean={stats['is_pure_korean']}"
    )

    if stats['chinese_chars'] > 0:
        non_korean = find_non_korean_chars(text, max_examples=5)
        examples = ", ".join([f"'{char}'" for char, _, _ in non_korean])
        logger.warning(f"[Language Warning] {field_name}: 한자 감지됨 - {examples}")
