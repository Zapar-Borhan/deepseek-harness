#!/usr/bin/env python3
"""A small, dependency-free harness for the DeepSeek chat API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


def build_payload(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    return payload


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(case, dict) or not isinstance(case.get("input"), str):
            raise ValueError(f"{path}:{line_number}: each case needs a string 'input'")
        case.setdefault("id", f"case-{len(cases) + 1}")
        cases.append(case)
    if not cases:
        raise ValueError(f"{path}: no cases found")
    return cases


def extract_text(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not choices or not isinstance(choices, list):
        raise ValueError("API response has no choices")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError("API response has no text content")
    return content


def call_deepseek(
    prompt: str,
    *,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    max_tokens: int | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    payload = build_payload(
        prompt,
        system=system,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach DeepSeek API: {exc.reason}") from exc


def run_case(
    case: dict[str, Any],
    *,
    api_key: str,
    base_url: str,
    default_model: str,
    temperature: float,
    max_tokens: int | None,
    timeout: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    prompt = case["input"]
    model = case.get("model", default_model)
    system = case.get("system")
    result: dict[str, Any] = {
        "id": case["id"],
        "input": prompt,
        "expected": case.get("expected"),
        "model": model,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        response = call_deepseek(
            prompt,
            api_key=api_key,
            base_url=base_url,
            system=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        result["status"] = "ok"
        result["output"] = extract_text(response)
        result["usage"] = response.get("usage")
    except (RuntimeError, ValueError) as exc:
        result["status"] = "error"
        result["error"] = str(exc)
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return result


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def require_api_key() -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is not set. Copy .env.example and export your key.")
    return api_key


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--timeout", type=float, default=60.0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run prompts against the DeepSeek chat API.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL),
        help="API base URL (default: https://api.deepseek.com)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser("ask", help="send one prompt")
    ask_parser.add_argument("prompt")
    ask_parser.add_argument("--system")
    add_common_options(ask_parser)

    run_parser = subparsers.add_parser("run", help="run JSONL cases")
    run_parser.add_argument("--cases", type=Path, default=Path("cases.jsonl"))
    run_parser.add_argument("--output", type=Path, default=Path("results/results.jsonl"))
    run_parser.add_argument("--system")
    add_common_options(run_parser)

    args = parser.parse_args()
    api_key = require_api_key()

    if args.command == "ask":
        response = call_deepseek(
            args.prompt,
            api_key=api_key,
            base_url=args.base_url,
            system=args.system,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )
        print(extract_text(response))
        return 0

    cases = load_cases(args.cases)
    rows = [
        run_case(
            case,
            api_key=api_key,
            base_url=args.base_url,
            default_model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )
        for case in cases
    ]
    write_jsonl(args.output, rows)
    passed = sum(row["status"] == "ok" for row in rows)
    print(f"Completed {len(rows)} cases: {passed} ok, {len(rows) - passed} errors")
    print(f"Results: {args.output}")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
