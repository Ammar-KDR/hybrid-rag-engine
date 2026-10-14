import re
from typing import Tuple, List

# Arabic Unicode Ranges
# Tashkeel / Diacritics: Fathatan to Sukun, Dagger Alif
TASHKEEL_REGEX = re.compile(r"[\u064B-\u065F\u0670]")
TATWEEL_REGEX = re.compile(r"\u0640")
ARABIC_CHAR_REGEX = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")

# Government Service Heading Keywords
GOV_HEADING_KEYWORDS = (
    "شروط",
    "الشروط",
    "متطلبات",
    "المتطلبات",
    "الوثائق",
    "وثائق",
    "المستندات",
    "مستندات",
    "الأوراق",
    "الأوراق المطلوبة",
    "الاوراق",
    "إجراءات",
    "الإجراءات",
    "اجراءات",
    "الاجراءات",
    "خطوات",
    "الخطوات",
    "مسار",
    "الرسوم",
    "رسوم",
    "المدة",
    "المده",
    "الوقت",
    "قنوات",
    "القنوات",
    "الفئات",
    "المستفيدون",
    "المستفيدين",
    "ملاحظات",
    "الملاحظات",
    "استثناءات",
    "الاستثناءات",
    "المعايير",
)

LEGAL_CLAUSE_REGEX = re.compile(
    r"^(المادة|الماده|البند|الفقرة|الفقره|الفصل|الباب)\s*([0-9\(\)\-أ-ي\s]+)[:\.\-]?",
    re.IGNORECASE,
)


def is_arabic_text(text: str) -> bool:
    """Returns True if the text contains any Arabic characters."""
    return bool(ARABIC_CHAR_REGEX.search(text))


def remove_tashkeel(text: str) -> str:
    """Strips Arabic diacritics / harakat."""
    return TASHKEEL_REGEX.sub("", text)


def remove_tatweel(text: str) -> str:
    """Strips Arabic kashida / tatweel (ـ)."""
    return TATWEEL_REGEX.sub("", text)


def normalize_arabic(text: str) -> str:
    """
    Standardizes Arabic text variations:
    - Normalizes Unicode Presentation Forms to standard Arabic characters
    - Strips tashkeel and tatweel
    - Unifies Alef variants (إ, أ, آ, ٱ -> ا)
    - Unifies Alef Maqsura to Yaa (ى -> ي)
    - Unifies Taa Marbuta to Haa (ة -> ه)
    """
    if not text:
        return ""
    import unicodedata

    text = unicodedata.normalize("NFKC", text)
    text = remove_tashkeel(text)
    text = remove_tatweel(text)
    # Normalize Alef variants
    text = re.sub(r"[إأآٱ]", "ا", text)
    # Normalize Alef Maqsura
    text = re.sub(r"ى", "ي", text)
    # Normalize Taa Marbuta
    text = re.sub(r"ة", "ه", text)
    return text.strip()


def tokenize_arabic(text: str) -> List[str]:
    """
    Tokenizes Arabic text for BM25 with normalization and prefix expansion.
    Produces the normalized base token and, when applicable, the stem without
    the definite article (ال-) or common coordinating prefixes.
    """
    normalized = normalize_arabic(text.lower())
    raw_tokens = re.findall(r"[\u0621-\u064A0-9a-zA-Z]+", normalized)
    
    tokens: List[str] = []
    for token in raw_tokens:
        tokens.append(token)
        # Prefix expansion for definite article (ال-)
        if token.startswith("ال") and len(token) > 3:
            stem = token[2:]
            tokens.append(stem)
        # Prefix expansion for coordinating particles (و/ف/ب/ل + ال)
        elif token.startswith(("وال", "فال", "بال", "لال")) and len(token) > 4:
            stem = token[3:]
            tokens.append(stem)
        elif token.startswith(("و", "ف", "ب", "ل")) and len(token) > 3:
            stem = token[1:]
            tokens.append(stem)

    return tokens


def is_arabic_heading(line: str) -> Tuple[bool, str, int]:
    """
    Determines if a given line corresponds to an Arabic government document section heading.
    Returns: (is_heading, heading_title, level)
    """
    stripped = line.strip()
    if not stripped:
        return False, "", 0

    # 1. Standard Markdown Heading
    md_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
    if md_match:
        level = len(md_match.group(1))
        title = md_match.group(2).strip()
        return True, title, level

    # 2. Legal Clause / Article (e.g. المادة (1): or البند أولاً)
    legal_match = LEGAL_CLAUSE_REGEX.match(stripped)
    if legal_match:
        clean_title = re.sub(r"[:：\-ـ\s]+$", "", stripped).strip()
        return True, clean_title, 2

    # 3. Government Service Guide Sections
    norm_line = normalize_arabic(stripped)
    stem_line = norm_line[2:] if norm_line.startswith("ال") else norm_line

    for kw in GOV_HEADING_KEYWORDS:
        norm_kw = normalize_arabic(kw)
        if norm_line.startswith(norm_kw) or stem_line.startswith(norm_kw):
            # Must end with punctuation or be a concise standalone label
            is_explicit_punct = stripped.endswith((":", "：", "-", "ـ"))
            is_concise_label = (
                len(stripped.split()) <= 5
                and not stripped.endswith((".", "!", "؟", "?"))
                and not any(c.isdigit() for c in stripped)
            )
            if is_explicit_punct or is_concise_label:
                clean_title = re.sub(r"[:：\-ـ\s]+$", "", stripped).strip()
                return True, clean_title, 2

    # 4. Ordinal sections (أولاً:, ثانياً:, etc.)
    if re.match(r"^(اولا|ثانيا|ثالثا|رابعا|خامسا|سادسا|سابعا|ثامنا|تاسعا|عاشرا)[:\.\-]", norm_line):
        clean_title = re.sub(r"[:：\-ـ\s]+$", "", stripped).strip()
        return True, clean_title, 2

    return False, "", 0


def split_arabic_sentences(text: str) -> List[str]:
    """
    Splits Arabic prose on sentence and clause boundaries (، ؛ . ؟ \n)
    while preserving meaningful chunks.
    """
    # Replace Arabic sentence delimiters with unique marker
    pattern = r"([.!?؛؟\n]+|[،,]\s+)"
    parts = re.split(pattern, text)
    
    sentences: List[str] = []
    current = ""
    
    for part in parts:
        if not part:
            continue
        current += part
        if re.search(pattern, part) or len(current) >= 150:
            trimmed = current.strip()
            if trimmed:
                sentences.append(trimmed)
            current = ""
            
    if current.strip():
        sentences.append(current.strip())
        
    return sentences
