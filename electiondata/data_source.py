from abc import ABC, abstractmethod

from permacache import permacache


class DataSource(ABC):
    @abstractmethod
    def version(self):
        pass

    @abstractmethod
    def description(self):
        pass

    @abstractmethod
    def get_direct(self):
        pass

    def get(self):
        print(self.description())
        return get(self)


@permacache(
    "electiondata/data_source/get",
    key_function=dict(
        source=lambda source: [source.version(), type(source).__name__, source.__dict__]
    ),
)
def get(source):
    return source.get_direct()
