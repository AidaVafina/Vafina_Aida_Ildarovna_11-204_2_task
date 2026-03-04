#!/usr/bin/env python3
"""Build token and lemma files for each document in the input directory."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup
import pymorphy3

TOKEN_RE = re.compile(r"[a-zа-яё]+(?:-[a-zа-яё]+)*", re.IGNORECASE)
VALID_TOKEN_RE = re.compile(r"[a-zа-яё]+(?:-[a-zа-яё]+)*", re.IGNORECASE)
MIXED_TOKEN_RE = re.compile(
    r"\b(?=\w*[a-zа-яё])(?=\w*\d)\w+\b", re.IGNORECASE
)
SUPPORTED_EXTENSIONS = {".txt", ".html", ".htm"}
EXCLUDED_POS = {"PREP", "CONJ", "PRCL", "INTJ", "NPRO"}
MARKUP_GARBAGE = {
    "amp",
    "class",
    "div",
    "href",
    "http",
    "https",
    "nbsp",
    "script",
    "span",
    "style",
    "www",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create per-document token and lemma files."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory with saved documents (.txt, .html, .htm).",
    )
    parser.add_argument(
        "--tokens-dir",
        type=Path,
        default=Path("data/results/tokens"),
        help="Directory for generated token files.",
    )
    parser.add_argument(
        "--lemmas-dir",
        type=Path,
        default=Path("data/results/lemmas"),
        help="Directory for generated lemma files.",
    )
    return parser.parse_args()


def read_document(path: Path) -> str:
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() not in {".html", ".htm"}:
        return raw_text

    soup = BeautifulSoup(raw_text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ")


def is_garbage_token(token: str) -> bool:
    if len(token) < 2:
        return True
    if any(char.isdigit() for char in token):
        return True
    return VALID_TOKEN_RE.fullmatch(token) is None


def extract_unique_tokens(text: str) -> list[str]:
    cleaned_text = MIXED_TOKEN_RE.sub(" ", text.lower())
    unique_tokens: set[str] = set()
    for token in TOKEN_RE.findall(cleaned_text):
        normalized = token.strip("-")
        if not normalized or is_garbage_token(normalized):
            continue
        if normalized in MARKUP_GARBAGE:
            continue
        unique_tokens.add(normalized)
    return sorted(unique_tokens)


def filter_service_tokens(tokens: list[str], morph: pymorphy3.MorphAnalyzer) -> list[str]:
    filtered: list[str] = []
    for token in tokens:
        parse = morph.parse(token)[0]
        pos = parse.tag.POS
        if pos in EXCLUDED_POS or pos == "NUMR":
            continue
        if parse.normal_form.isdigit():
            continue
        filtered.append(token)
    return filtered


def build_lemma_index(
    tokens: list[str], morph: pymorphy3.MorphAnalyzer
) -> dict[str, list[str]]:
    lemma_to_tokens: defaultdict[str, set[str]] = defaultdict(set)
    for token in tokens:
        lemma = morph.parse(token)[0].normal_form
        lemma_to_tokens[lemma].add(token)

    return {
        lemma: sorted(token_forms)
        for lemma, token_forms in sorted(lemma_to_tokens.items(), key=lambda item: item[0])
    }


def write_token_file(path: Path, tokens: list[str]) -> None:
    content = "".join(f"{token}\n" for token in tokens)
    path.write_text(content, encoding="utf-8")


def write_lemma_file(path: Path, lemma_index: dict[str, list[str]]) -> None:
    lines = [f"{lemma} {' '.join(forms)}\n" for lemma, forms in lemma_index.items()]
    path.write_text("".join(lines), encoding="utf-8")


def process_document(
    file_path: Path,
    tokens_dir: Path,
    lemmas_dir: Path,
    morph: pymorphy3.MorphAnalyzer,
) -> tuple[Path, Path]:
    document_text = read_document(file_path)
    unique_tokens = extract_unique_tokens(document_text)
    content_tokens = filter_service_tokens(unique_tokens, morph)
    lemma_index = build_lemma_index(content_tokens, morph)

    output_base = file_path.stem
    token_path = tokens_dir / f"{output_base}_tokens.txt"
    lemma_path = lemmas_dir / f"{output_base}_lemmas.txt"

    write_token_file(token_path, content_tokens)
    write_lemma_file(lemma_path, lemma_index)

    return token_path, lemma_path


def main() -> None:
    args = parse_args()
    args.tokens_dir.mkdir(parents=True, exist_ok=True)
    args.lemmas_dir.mkdir(parents=True, exist_ok=True)

    input_files = sorted(
        path
        for path in args.input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not input_files:
        raise FileNotFoundError(
            f"No input documents found in '{args.input_dir}'. "
            "Place .txt, .html or .htm files there."
        )

    morph = pymorphy3.MorphAnalyzer()
    for input_file in input_files:
        token_file, lemma_file = process_document(
            file_path=input_file,
            tokens_dir=args.tokens_dir,
            lemmas_dir=args.lemmas_dir,
            morph=morph,
        )
        print(f"[OK] {input_file.name} -> {token_file.name}, {lemma_file.name}")


if __name__ == "__main__":
    main()
