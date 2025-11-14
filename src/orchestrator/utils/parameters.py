from enum import Enum, auto


class RunStatus(Enum):
    STARTED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()

class RunStage(Enum):
    ORCHESTRATION = auto()
    SCRAPING = auto()
    TRANSFORMATION = auto()


class FlowType(Enum):
    DAILY = auto()
    CUSTOM = auto()
    BACKFILL = auto()


