# -*- coding: utf-8 -*-
import re
import sys
import argparse
from mappings import *

# --- Pre-computed structures ---

COMPOUNDS_FIRST = {
    "ch": "ч",
    "Ch": "Ч",
    "CH": "Ч",
    "sh": "ш",
    "Sh": "Ш",
    "SH": "Ш",
    "yo‘": "йў",
    "Yo‘": "Йў",
    "YO‘": "ЙЎ",
}

COMPOUNDS_SECOND = {
    "yo": "ё",
    "Yo": "Ё",
    "YO": "Ё",
    "yu": "ю",
    "Yu": "Ю",
    "YU": "Ю",
    "ya": "я",
    "Ya": "Я",
    "YA": "Я",
    "ye": "е",
    "Ye": "Е",
    "YE": "Е",
    "o‘": "ў",
    "O‘": "Ў",
    "oʻ": "ў",
    "Oʻ": "Ў",
    "g‘": "ғ",
    "G‘": "Ғ",
    "gʻ": "ғ",
    "Gʻ": "Ғ",
}

BEGINNING_RULES_CYR = {
    "ye": "е",
    "Ye": "Е",
    "YE": "Е",
    "e": "э",
    "E": "Э",
}

AFTER_VOWEL_RULES_CYR = {
    "ye": "е",
    "Ye": "Е",
    "YE": "Е",
    "e": "э",
    "E": "Э",
}

EXCEPTION_WORDS_RULES = {
    "s": "ц",
    "S": "Ц",
    "ts": "ц",
    "Ts": "Ц",
    "TS": "Ц",
    "e": "э",
    "E": "э",
    "sh": "сҳ",
    "Sh": "Сҳ",
    "SH": "СҲ",
    "yo": "йо",
    "Yo": "Йо",
    "YO": "ЙО",
    "yu": "йу",
    "Yu": "Йу",
    "YU": "ЙУ",
    "ya": "йа",
    "Ya": "Йа",
    "YA": "ЙА",
    "ye": "йе",
    "Ye": "Йе",
    "YE": "ЙЕ",
}

BEGINNING_RULES_LAT = {"ц": "s", "Ц": "S", "е": "ye", "Е": "Ye"}

AFTER_VOWEL_RULES_LAT = {"ц": "ts", "Ц": "Ts", "е": "ye", "Е": "Ye"}

# --- Compile Regexes ---

# 1. Soft Sign Words
# O(N) regex for replacing whole words
# Sort by length desc to ensure longest match
SOFT_SIGN_KEYS = sorted(SOFT_SIGN_WORDS.keys(), key=len, reverse=True)
SOFT_SIGN_PATTERN = re.compile(
    r"\b(%s)\b" % "|".join(map(re.escape, SOFT_SIGN_KEYS)), re.U | re.IGNORECASE
)


def replace_soft_sign_words(m):
    word = m.group(1)
    lower_word = word.lower()
    if lower_word not in SOFT_SIGN_WORDS:
        return word

    result = SOFT_SIGN_WORDS[lower_word]

    # Match case of input
    if word.isupper():
        return result.upper()
    elif word[0].isupper():
        return result[0].upper() + result[1:]
    else:
        return result


# 2. Exception Words (TS_WORDS, E_WORDS, etc.)
EXCEPTION_MAPPING = {}
# Include all exception dictionaries
all_exception_dicts = [
    TS_WORDS,
    E_WORDS,
    SH_WORDS,
    YO_WORDS,
    YU_WORDS,
    YA_WORDS,
    YE_WORDS,
]
for d in all_exception_dicts:
    for key in d:
        clean = key.replace("(", "").replace(")", "")
        EXCEPTION_MAPPING[clean] = key

# Sort by length desc
EXCEPTION_KEYS_SORTED = sorted(EXCEPTION_MAPPING.keys(), key=len, reverse=True)
EXCEPTION_WORDS_PATTERN = re.compile(
    r"\b(%s)\b" % "|".join(map(re.escape, EXCEPTION_KEYS_SORTED)), re.U | re.IGNORECASE
)


def replace_exception_matches(m):
    word = m.group(1)
    lower_word = word.lower()
    if lower_word not in EXCEPTION_MAPPING:
        return word

    template = EXCEPTION_MAPPING[lower_word]
    # template format: prefix(target)suffix
    # We find the paren indices in template
    start_paren = template.find("(")
    end_paren = template.find(")")

    if start_paren == -1 or end_paren == -1:
        return word

    prefix_len = start_paren
    target_len = end_paren - start_paren - 1

    # Map offsets to matched word
    word_target = word[prefix_len : prefix_len + target_len]

    # Lookup in rules
    if word_target in EXCEPTION_WORDS_RULES:
        mapped = EXCEPTION_WORDS_RULES[word_target]
    else:
        # Fallback for Mixed Case not explicitly in rules (e.g. tS)
        mapped = word_target

    return word[:prefix_len] + mapped + word[prefix_len + target_len :]


# 3. Compounds and other rules
COMPOUNDS_FIRST_PATTERN = re.compile(
    r"(%s)" % "|".join(map(re.escape, COMPOUNDS_FIRST.keys())), re.U
)
COMPOUNDS_SECOND_PATTERN = re.compile(
    r"(%s)" % "|".join(map(re.escape, COMPOUNDS_SECOND.keys())), re.U
)

BEGINNING_RULES_CYR_PATTERN = re.compile(
    r"\b(%s)" % "|".join(map(re.escape, BEGINNING_RULES_CYR.keys())), re.U
)
# Note: LATIN_VOWELS is a tuple, no need to escape if known safe, but good practice.
# AFTER_VOWEL_RULES: (vowel)(target)
AFTER_VOWEL_RULES_CYR_PATTERN = re.compile(
    r"(%s)(%s)"
    % (
        "|".join(map(re.escape, LATIN_VOWELS)),
        "|".join(map(re.escape, AFTER_VOWEL_RULES_CYR.keys())),
    ),
    re.U,
)

LATIN_TO_CYRILLIC_PATTERN = re.compile(
    r"(%s)" % "|".join(map(re.escape, LATIN_TO_CYRILLIC.keys())), re.U
)

# Latin Conversion Patterns
CYR_TO_LAT_SENT_OKT_PATTERN = re.compile(r"(сент|окт)([яЯ])(бр)", re.IGNORECASE | re.U)
BEGINNING_RULES_LAT_PATTERN = re.compile(
    r"\b(%s)" % "|".join(map(re.escape, BEGINNING_RULES_LAT.keys())), re.U
)
AFTER_VOWEL_RULES_LAT_PATTERN = re.compile(
    r"(%s)(%s)"
    % (
        "|".join(map(re.escape, CYRILLIC_VOWELS)),
        "|".join(map(re.escape, AFTER_VOWEL_RULES_LAT.keys())),
    ),
    re.U,
)
CYRILLIC_TO_LATIN_PATTERN = re.compile(
    r"(%s)" % "|".join(map(re.escape, CYRILLIC_TO_LATIN.keys())), re.U
)


def to_cyrillic(text):
    # standardize some characters
    text = text.replace("ʻ", "‘")

    # 1. Exception words (soft sign words)
    text = SOFT_SIGN_PATTERN.sub(replace_soft_sign_words, text)

    # 2. Other exception words (ts, e, sh...)
    text = EXCEPTION_WORDS_PATTERN.sub(replace_exception_matches, text)

    # 3. Compounds (ch, sh...)
    text = COMPOUNDS_FIRST_PATTERN.sub(lambda x: COMPOUNDS_FIRST[x.group(1)], text)
    text = COMPOUNDS_SECOND_PATTERN.sub(lambda x: COMPOUNDS_SECOND[x.group(1)], text)

    # 4. Contextual Rules (beginning of word / after vowel)
    text = BEGINNING_RULES_CYR_PATTERN.sub(
        lambda x: BEGINNING_RULES_CYR[x.group(1)], text
    )
    text = AFTER_VOWEL_RULES_CYR_PATTERN.sub(
        lambda x: "%s%s" % (x.group(1), AFTER_VOWEL_RULES_CYR[x.group(2)]), text
    )

    # 5. Basic Mapping
    text = LATIN_TO_CYRILLIC_PATTERN.sub(lambda x: LATIN_TO_CYRILLIC[x.group(1)], text)

    return text


def to_latin(text):
    # 1. Special Months handling (Sentabr/Oktabr)
    text = CYR_TO_LAT_SENT_OKT_PATTERN.sub(
        lambda x: "%s%s%s"
        % (x.group(1), "a" if x.group(2) == "я" else "A", x.group(3)),
        text,
    )

    # 2. Contextual Rules
    text = BEGINNING_RULES_LAT_PATTERN.sub(
        lambda x: BEGINNING_RULES_LAT[x.group(1)], text
    )
    text = AFTER_VOWEL_RULES_LAT_PATTERN.sub(
        lambda x: "%s%s" % (x.group(1), AFTER_VOWEL_RULES_LAT[x.group(2)]), text
    )

    # 3. Basic Mapping
    text = CYRILLIC_TO_LATIN_PATTERN.sub(lambda x: CYRILLIC_TO_LATIN[x.group(1)], text)

    return text


def transliterate(text, to_variant):
    if to_variant == "cyrillic":
        text = to_cyrillic(text)
    elif to_variant == "latin":
        text = to_latin(text)
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Transliterate Uzbek text between Latin and Cyrillic."
    )
    # Using 'store' for input to support file path or stdin
    # Actually argparse FileType is good but let's stick to simple file path logic to avoid open file issues if not needed
    # But for a simple script, FileType is easy.
    parser.add_argument(
        "input_file",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="Input file path (default: stdin)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w", encoding="utf-8"),
        default=sys.stdout,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "-t",
        "--to",
        choices=["cyrillic", "latin"],
        default="cyrillic",
        help='Target script: "cyrillic" (default) or "latin"',
    )

    args = parser.parse_args()

    try:
        if args.input_file == sys.stdin:
            # stdin might not have encoding set if piped?
            # PYTHONIOENCODING usually handles it, or use sys.stdin.read() with decode.
            # But standard iteration is usually fine in Py3.
            pass

        for line in args.input_file:
            args.output.write(
                transliterate(
                    line, args.to_variant if hasattr(args, "to_variant") else args.to
                )
            )

    except BrokenPipeError:
        pass
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
