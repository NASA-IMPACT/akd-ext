"""Inverse of ``WorldviewPermalinkTool.build_url``.

Parses a Worldview permalink URL into a ``WorldviewPermalinkInputSchema``.

The combination of this module + the adapter gives the round-trip:

    URL → WorldviewPermalinkInputSchema → GeoIntent → ...
                                                    → GeoIntent → WorldviewPermalinkInputSchema → URL
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from akd_ext.tools.worldview.permalink import LayerSpec, WorldviewPermalinkInputSchema

_LAYER_FLAG_KEYS = frozenset({"hidden", "squash"})
_LAYER_LIST_KEYS = frozenset({"palettes"})


def _split_top_level(s: str, sep: str = ",") -> list[str]:
    """Split on ``sep`` at parenthesis depth 0.

    Required because Worldview's layer-list grammar uses ``,`` both as
    a top-level layer separator and as a modifier separator inside
    ``(...)`` groups.
    """
    out: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in s:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif ch == sep and depth == 0:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf))
    return out


def _parse_layer_modifiers(mods: str) -> dict:
    """Parse the comma-separated modifier list inside a layer's parentheses.

    Handles the palettes-list quirk: ``palettes=red_1,red_2`` keeps both
    values for palettes; tokens without ``=`` that follow a list-typed
    modifier are treated as continuation values for that list.
    """
    tokens = mods.split(",")
    result: dict = {}
    current_list_key: str | None = None

    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        if tok in _LAYER_FLAG_KEYS:
            result[tok] = True
            current_list_key = None
        elif "=" in tok:
            key, _, value = tok.partition("=")
            if key in _LAYER_LIST_KEYS:
                result.setdefault(key, []).append(value)
                current_list_key = key
            elif key == "opacity":
                result[key] = float(value)
                current_list_key = None
            elif key in {"min", "max"}:
                result[key] = float(value)
                current_list_key = None
            elif key == "style":
                result[key] = value
                current_list_key = None
            else:
                current_list_key = None
        else:
            if current_list_key is not None:
                result[current_list_key].append(tok)
    return result


def _parse_layer(spec: str) -> LayerSpec:
    """Parse one layer token: ``NAME`` or ``NAME(mod1,mod2,...)``."""
    if "(" not in spec:
        return LayerSpec(id=spec)
    name, _, rest = spec.partition("(")
    if not rest.endswith(")"):
        raise ValueError(f"Unmatched parenthesis in layer spec: {spec!r}")
    mods = _parse_layer_modifiers(rest[:-1])
    return LayerSpec(id=name, **mods)


def _parse_layer_list(value: str) -> list[LayerSpec]:
    return [_parse_layer(s) for s in _split_top_level(value, ",") if s]


def _parse_coord_list(value: str, *, n: int) -> list[float]:
    parts = value.split(",")
    if len(parts) != n:
        raise ValueError(f"expected {n} comma-separated numbers; got {value!r}")
    return [float(p) for p in parts]


def parse_url(url: str) -> WorldviewPermalinkInputSchema:
    """Parse a Worldview permalink URL into a ``WorldviewPermalinkInputSchema``.

    Round-trip property: ``build_url(parse_url(u))`` yields a URL with
    the same logical state as ``u`` (parameter order may differ; the
    ``em=true`` housekeeping flag is dropped on parse and re-added on
    re-build).
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    flat: dict[str, str] = {k: v[0] for k, v in qs.items() if v}

    fields: dict = {"layers": _parse_layer_list(flat["l"]) if "l" in flat else []}

    if "p" in flat:
        fields["projection"] = flat["p"]
    if "t" in flat:
        fields["time"] = flat["t"]
    if "v" in flat:
        fields["bbox"] = _parse_coord_list(flat["v"], n=4)
    if "r" in flat:
        fields["rotation"] = float(flat["r"])

    if "ca" in flat:
        fields["compare_active"] = flat["ca"].lower() == "true"
        if "l1" in flat:
            fields["compare_layers"] = _parse_layer_list(flat["l1"])
        if "t1" in flat:
            fields["compare_time"] = flat["t1"]
        if "cm" in flat:
            fields["compare_mode"] = flat["cm"]
        if "cv" in flat:
            fields["compare_value"] = int(flat["cv"])

    if "cha" in flat:
        fields["chart_active"] = flat["cha"].lower() == "true"
        if "chl" in flat:
            fields["chart_layer"] = flat["chl"]
        if "chc" in flat:
            fields["chart_area"] = _parse_coord_list(flat["chc"], n=4)
        if "cht" in flat:
            fields["chart_time_start"] = flat["cht"]
        if "cht2" in flat:
            fields["chart_time_end"] = flat["cht2"]
        if "chch" in flat:
            fields["chart_autoload"] = flat["chch"].lower() == "true"

    return WorldviewPermalinkInputSchema(**fields)
