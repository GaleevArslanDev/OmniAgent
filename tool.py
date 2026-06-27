from abc import ABC, abstractmethod
from typing import Any

class Tool(ABC):
    name: str
    description: str
    args_schema: dict

    @abstractmethod
    def use(self, client, arguments: dict) -> tuple[bool, Any | None]:
        pass