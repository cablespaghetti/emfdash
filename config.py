import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FeedConfig:
    topic: str
    emoji: str


@dataclass
class Config:
    favourites_url: str | None = None
    feeds: list[FeedConfig] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path = "config.toml") -> "Config":
        p = Path(path)
        if not p.exists():
            return cls()
        with open(p, "rb") as f:
            data = tomllib.load(f)
        raw_feeds = data.get("feeds", [])
        feeds = [FeedConfig(**f) for f in raw_feeds]
        return cls(
            favourites_url=data.get("favourites", {}).get("url"),
            feeds=feeds,
        )
