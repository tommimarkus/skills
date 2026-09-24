"""Immutable reference behavior for the evaluation fixture."""


def expected_slug(value: str) -> str:
    pieces: list[str] = []
    separated = False
    for character in value:
        if "A" <= character <= "Z" or "a" <= character <= "z" or "0" <= character <= "9":
            pieces.append(character.lower())
            separated = False
        elif pieces and not separated:
            pieces.append("-")
            separated = True
    return "".join(pieces).rstrip("-")


def expected_unique_labels(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        key = stripped.casefold()
        if stripped and key not in seen:
            result.append(stripped)
            seen.add(key)
    return result
