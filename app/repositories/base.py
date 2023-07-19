from abc import ABC, abstractmethod


class BaseDBRepository(ABC):
    model = None

    @abstractmethod
    async def get(self):
        pass

    @abstractmethod
    async def post(self):
        pass

    @abstractmethod
    async def delete(self):
        pass

    @abstractmethod
    async def update(self):
        pass

    @abstractmethod
    async def get_all_paginated(self):
        pass



