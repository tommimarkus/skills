from __future__ import annotations

import datetime as dt

from .errors import invalid_policy
from .strategy_calver_format import calver_regex, render_calver, tokenize_scheme


def calver_default(request):
    tokens = tokenize_scheme(request.scheme)
    if request.bump:
        return request.bump
    return "build" if "build" in tokens or "micro" in tokens else "date"


def bump_calver(request):
    date_value = parse_date(request.date)
    tokens = tokenize_scheme(request.scheme)
    if "build" not in tokens and "micro" not in tokens:
        return render_calver(request.scheme, date_value, None)
    regex = calver_regex(request.scheme, date_value)
    numbers = matching_build_numbers(regex, [request.current, *request.existing_tags])
    return render_calver(request.scheme, date_value, max(numbers, default=0) + 1)


def parse_date(value):
    if not value:
        return dt.date.today()
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise invalid_policy(f"--date must be YYYY-MM-DD: {value}") from exc


def matching_build_numbers(regex, values):
    numbers = []
    for value in values:
        if not value:
            continue
        match = regex.match(normalize_tag(value))
        if match:
            numbers.append(int(match.group("build")))
    return numbers


def normalize_tag(value):
    stripped = value.strip()
    return stripped[1:] if stripped.startswith("v") else stripped
