from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class TileDef:
    type: str
    weight: int = 1
    topic: str | None = None
    emoji: str | None = None
    mode: str | None = None
    url: str | None = None
    accounts: list[str] | None = None
    hashtag: str | None = None


@dataclass
class RowDef:
    weight: int = 1
    tiles: list[TileDef] = field(default_factory=list)


@dataclass
class ColumnDef:
    weight: int = 1
    rows: list[RowDef] = field(default_factory=list)


@dataclass
class LayoutDef:
    columns: list[ColumnDef]


def _parse_tile(raw: dict) -> TileDef:
    return TileDef(
        type=raw["type"],
        weight=raw.get("weight", 1),
        topic=raw.get("topic"),
        emoji=raw.get("emoji"),
        mode=raw.get("mode"),
        url=raw.get("url"),
        accounts=raw.get("accounts"),
        hashtag=raw.get("hashtag"),
    )


def _parse_rows(raw_rows: list[dict]) -> list[RowDef]:
    rows = []
    for r in raw_rows:
        weight = r.get("weight", 1)
        if r.get("type") == "hsplit" and "tiles" in r:
            tiles = [_parse_tile(t) for t in r["tiles"]]
        else:
            tiles = [_parse_tile(r)]
        rows.append(RowDef(weight=weight, tiles=tiles))
    return rows


def _parse_layout(data: dict) -> LayoutDef:
    raw_cols = data.get("columns")
    if not raw_cols:
        raise ValueError("no columns defined in config.yaml")
    columns = []
    for c in raw_cols:
        columns.append(
            ColumnDef(
                weight=c.get("weight", 1),
                rows=_parse_rows(c.get("rows", [])),
            )
        )
    return LayoutDef(columns=columns)


@dataclass
class Config:
    layout: LayoutDef

    @classmethod
    def load(cls, path: str | Path = "config.yaml") -> "Config":
        p = Path(path)
        if not p.exists():
            raise ValueError(f"{path} not found")
        with open(p) as f:
            data = yaml.safe_load(f) or {}
        return cls(
            layout=_parse_layout(data),
        )
