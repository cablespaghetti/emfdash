import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    favourites_url: str | None = None

    @classmethod
    def load(cls, path: str | Path = "config.toml") -> "Config":
        p = Path(path)
        if not p.exists():
            return cls()
        with open(p, "rb") as f:
            data = tomllib.load(f)
        return cls(
            favourites_url=data.get("favourites", {}).get("url"),
        )
