from abc import ABC, abstractmethod
from typing import Optional


class DBBackend(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def store_user(self, user_details: dict) -> bool:
        raise NotImplementedError
