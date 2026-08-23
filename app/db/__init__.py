from abc import ABC, abstractmethod
from typing import Optional


class DBBackend(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def store_user(self, user_details: dict) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_cache(self, key: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def set_cache(self, key: str, value: dict, ttl_seconds: int) -> bool:
        raise NotImplementedError
