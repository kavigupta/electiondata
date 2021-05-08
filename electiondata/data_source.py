from abc import ABC, abstractmethod

from permacache import permacache


class DataSource(ABC):
    @abstractmethod
    def version(self):
        pass

    @abstractmethod
    def get(self):
        pass

    def get_cached(self):
        return get(self)


@permacache(
    "electiondata/data_source/get",
    key_function=dict(source=lambda source: [source.version(), type(source).__name__]),
)
def get(source):
    return source.get()
