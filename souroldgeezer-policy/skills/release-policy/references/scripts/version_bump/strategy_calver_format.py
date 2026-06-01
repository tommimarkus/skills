from __future__ import annotations

import re

from .errors import invalid_policy


CALVER_TOKENS = ("YYYY", "YY", "build", "micro", "MM", "DD", "M", "D")


def tokenize_scheme(scheme):
    tokens = []
    index = 0
    while index < len(scheme):
        token = next((item for item in CALVER_TOKENS if scheme.startswith(item, index)), None)
        tokens.append(token or scheme[index])
        index += len(token or scheme[index])
    return tokens


def render_calver(scheme, date_value, build):
    return "".join(render_token(token, date_value, build, scheme) for token in tokenize_scheme(scheme))


def render_token(token, date_value, build, scheme):
    date_tokens = {
        "YYYY": f"{date_value.year:04d}",
        "YY": f"{date_value.year % 100:02d}",
        "MM": f"{date_value.month:02d}",
        "M": str(date_value.month),
        "DD": f"{date_value.day:02d}",
        "D": str(date_value.day),
    }
    if token in date_tokens:
        return date_tokens[token]
    if token in {"build", "micro"}:
        if build is None:
            raise invalid_policy(f"scheme {scheme} requires a build value")
        return str(build)
    return token


def calver_regex(scheme, date_value):
    parts = []
    for token in tokenize_scheme(scheme):
        if token in {"build", "micro"}:
            parts.append(r"(?P<build>\d+)")
        else:
            parts.append(re.escape(render_token(token, date_value, None, scheme)))
    return re.compile("^" + "".join(parts) + "$")
