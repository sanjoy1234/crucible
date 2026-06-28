"""Codebase fingerprinting — lightweight signature of language, framework, and risk surface."""

from __future__ import annotations

import re


def fingerprint_spec(spec: str) -> str:
    """
    Produce a short fingerprint string for a spec or code snippet.
    Used as metadata in the Knowledge Forge to cluster similar codebases.
    """
    signals = []

    if re.search(r"\bdjango\b|\bDjango\b|from django", spec):
        signals.append("django")
    elif re.search(r"\bflask\b|\bFlask\b|from flask", spec):
        signals.append("flask")
    elif re.search(r"\bfastapi\b|\bFastAPI\b|from fastapi", spec):
        signals.append("fastapi")
    elif re.search(r"\bspring\b|@Controller|@RestController", spec):
        signals.append("spring")
    elif re.search(r"\bexpress\b|require\('express'\)", spec):
        signals.append("express")

    if re.search(r"\basync\s+def\b|\bawait\b|\basyncio\b", spec):
        signals.append("async")
    if re.search(r"sqlite3|psycopg2|sqlalchemy|cursor\.execute", spec):
        signals.append("sql_direct")
    if re.search(r"\brequests\.get\b|\bhttpx\b|\baiohttp\b|fetch\(", spec):
        signals.append("http_client")
    if re.search(r"subprocess|os\.system|os\.popen|shell=True", spec):
        signals.append("shell_exec")
    if re.search(r"pickle|yaml\.load\b|json\.loads", spec):
        signals.append("deserialization")
    if re.search(r"password|secret|token|api_key|credential", spec, re.IGNORECASE):
        signals.append("credentials")

    lang = _detect_language(spec)
    signals.insert(0, lang)

    return ":".join(signals) if signals else "unknown"


def _detect_language(text: str) -> str:
    if re.search(r"\bdef\b|\bimport\b|\bclass\b.*:", text):
        return "python"
    if re.search(r"\bfunction\b|\bconst\b|\blet\b|\bvar\b|=>", text):
        return "typescript" if re.search(r":\s*(string|number|boolean|void)\b", text) else "javascript"
    if re.search(r"\bpublic\s+class\b|\bSystem\.out\b", text):
        return "java"
    if re.search(r"\bfunc\s+\w+\(|\bpackage\s+main\b", text):
        return "go"
    return "unknown"
