from api.models.DataOperationResult import  DataOperationResult
from typing import Optional, Sequence, TypeVar


class iDataService:

    T = TypeVar('T')

    def get_by_id(self,loadInactive:bool = False) -> T:
        raise NotImplementedError
    def save(self, dataObject: T):
        raise NotImplementedError
    def delete_by_id(self, id) -> DataOperationResult:
        raise NotImplementedError
    def query(self, query_object: object) -> [T]: #actually returns an array.  must be handled as such
        raise NotImplementedError

    # __all__ = ['paginate']