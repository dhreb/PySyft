# stdlib
from enum import Enum
from functools import partial
import os
from pathlib import Path
import tempfile
from typing import Any
from typing import Callable
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Type
from typing import Union

# third party
import networkx as nx
import pydantic
from result import Err
from result import Ok
from result import Result
from typing_extensions import Self

# relative
from ...node.credentials import SyftVerifyKey
from ...serde.deserialize import _deserialize
from ...serde.serializable import serializable
from ...serde.serialize import _serialize
from ...store.document_store import QueryKey
from ...store.document_store import QueryKeys
from ...store.document_store import StoreClientConfig
from ...store.document_store import StoreConfig
from ...store.locks import FileLockingConfig
from ...store.locks import LockingConfig
from ...store.locks import SyftLock
from ...types.datetime import DateTime
from ...types.syft_object import PartialSyftObject
from ...types.syft_object import SYFT_OBJECT_VERSION_1
from ...types.syft_object import SyftObject
from ...types.uid import UID
from .action_object import Action
from .action_object import ActionObject


@serializable()
class ExecutionStatus(Enum):
    PROCESSING = 0
    DONE = 1
    FAILED = 2


@serializable()
class NodeType(Enum):
    ACTION = Action
    ACTION_OBJECT = ActionObject


@serializable()
class NodeActionData(SyftObject):
    __canonical_name__ = "NodeActionData"
    __version__ = SYFT_OBJECT_VERSION_1

    id: Optional[UID]
    type: NodeType
    status: ExecutionStatus = ExecutionStatus.PROCESSING
    retry: int = 0
    created_at: Optional[DateTime]
    updated_at: Optional[DateTime]
    user_verify_key: SyftVerifyKey
    is_mutated: bool = False

    @pydantic.validator("created_at", pre=True, always=True)
    def make_created_at(cls, v: Optional[DateTime]) -> DateTime:
        return DateTime.now() if v is None else v

    @staticmethod
    def from_action(action: Action, credentials: SyftVerifyKey):
        return NodeActionData(
            id=action.id,
            type=NodeType.ACTION,
            user_verify_key=credentials,
        )

    @staticmethod
    def from_action_obj(action_obj: ActionObject, credentials: SyftVerifyKey):
        return NodeActionData(
            id=action_obj.id,
            type=NodeType.ACTION_OBJECT,
            user_verify_key=credentials,
        )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: Self):
        if not isinstance(other, NodeActionData):
            raise NotImplementedError(
                "Comparisions can be made with NodeActionData type objects only."
            )
        return hash(self) == hash(other)

    def __repr__(self):
        return self._repr_debug_()


@serializable()
class NodeActionDataUpdate(PartialSyftObject):
    __canonical_name__ = "NodeActionDataUpdate"
    __version__ = SYFT_OBJECT_VERSION_1

    id: Optional[UID]
    type: NodeType
    status: ExecutionStatus
    retry: int
    created_at: DateTime
    updated_at: DateTime
    credentials: SyftVerifyKey
    is_mutated: bool

    @pydantic.validator("updated_at", pre=True, always=True)
    def make_updated_at(cls, v: DateTime | None) -> DateTime:
        return DateTime.now() if v is None else v


@serializable()
class BaseGraphStore:
    graph_type: Any
    client_config: Optional[StoreClientConfig]

    def set(self, uid: Any, data: Any) -> None:
        raise NotImplementedError

    def get(self, uid: Any) -> Any:
        raise NotImplementedError

    def delete(self, uid: Any) -> None:
        raise NotImplementedError

    def find_neighbors(self, uid: Any) -> List[Any]:
        raise NotImplementedError

    def update(self, uid: Any, data: Any) -> None:
        raise NotImplementedError

    def add_edge(self, parent: Any, child: Any) -> None:
        raise NotImplementedError

    def remove_edge(self, parent: Any, child: Any) -> None:
        raise NotImplementedError

    def nodes(self) -> Any:
        raise NotImplementedError

    def edges(self) -> Any:
        raise NotImplementedError

    def visualize(self) -> None:
        raise NotImplementedError

    def save(self) -> None:
        raise NotImplementedError

    def get_predecessors(self, uid: UID) -> List:
        raise NotImplementedError

    def get_successors(self, uid: UID) -> List:
        raise NotImplementedError

    def exists(self, uid: Any) -> bool:
        raise NotImplementedError

    def subgraph(self, qks: QueryKeys) -> Any:
        raise NotImplementedError

    def topological_sort(self, subgraph: Any) -> Any:
        raise NotImplementedError


@serializable()
class InMemoryStoreClientConfig(StoreClientConfig):
    filename: Optional[str] = None
    path: Union[str, Path]

    def __init__(
        self,
        filename: Optional[str] = None,
        path: Optional[Union[str, Path]] = None,
        *args,
        **kwargs,
    ):
        path_ = tempfile.gettempdir() if path is None else path
        filename_ = "action_graph.bytes" if filename is None else filename
        super().__init__(filename=filename_, path=path_, *args, **kwargs)

    @property
    def file_path(self) -> Optional[Path]:
        return Path(self.path) / self.filename if self.filename is not None else None


@serializable()
class NetworkXBackingStore(BaseGraphStore):
    def __init__(self, store_config: StoreConfig) -> None:
        self.path_str = store_config.client_config.file_path.as_posix()

        if os.path.exists(self.path_str):
            self._db = self._load_from_path(self.path_str)
        else:
            self._db = nx.DiGraph()

        self.lock = SyftLock(store_config.locking_config)

    @property
    def db(self) -> nx.Graph:
        return self._db

    def _thread_safe_cbk(self, cbk: Callable, *args, **kwargs):
        # TODO copied method from document_store, have it in one place and reuse?
        locked = self.lock.acquire(blocking=True)
        if not locked:
            return Err("Failed to acquire lock for the operation")
        try:
            result = cbk(*args, **kwargs)
        except BaseException as e:
            result = Err(str(e))
        self.lock.release()

        return result

    def set(self, uid: UID, data: Any) -> None:
        self._thread_safe_cbk(self._set, uid=uid, data=data)

    def _set(self, uid: UID, data: Any) -> None:
        if self.exists(uid=uid):
            self.update(uid=uid, data=data)
        else:
            self.db.add_node(uid, data=data)
        self.save()

    def get(self, uid: UID) -> Any:
        node_data = self.db.nodes.get(uid)
        return node_data.get("data")

    def delete(self, uid: UID) -> None:
        self._thread_safe_cbk(self._delete, uid=uid)

    def _delete(self, uid: UID) -> None:
        if self.exists(uid=uid):
            self.db.remove_node(uid)
        self.save()

    def find_neighbors(self, uid: UID) -> Optional[List]:
        if self.exists(uid=uid):
            neighbors = self.graph.neighbors(uid)
            return neighbors

    def update(self, uid: UID, data: Any) -> None:
        self._thread_safe_cbk(self._update, uid=uid, data=data)

    def _update(self, uid: UID, data: Any) -> None:
        if self.exists(uid=uid):
            self.db.nodes[uid]["data"] = data
        self.save()

    def add_edge(self, parent: Any, child: Any) -> None:
        self._thread_safe_cbk(self._add_edge, parent=parent, child=child)

    def _add_edge(self, parent: Any, child: Any) -> None:
        self.db.add_edge(parent, child)
        self.save()

    def remove_edge(self, parent: Any, child: Any) -> None:
        self._thread_safe_cbk(self._remove_edge, parent=parent, child=child)

    def _remove_edge(self, parent: Any, child: Any) -> None:
        self.db.remove_edge(parent, child)
        self.save()

    def visualize(self) -> None:
        return nx.draw_networkx(self.db, with_labels=True)

    def nodes(self) -> Iterable:
        return self.db.nodes(data=True)

    def edges(self) -> Iterable:
        return self.db.edges()

    def get_predecessors(self, uid: UID) -> Iterable:
        return self.db.predecessors(uid)

    def get_successors(self, uid: UID) -> Iterable:
        return self.db.successors(uid)

    def is_parent(self, parent: Any, child: Any) -> bool:
        parents = self.db.predecessors(child)
        return parent in parents

    def save(self) -> None:
        bytes = _serialize(self.db, to_bytes=True)
        with open(self.path_str, "wb") as f:
            f.write(bytes)

    def _filter_nodes_by(self, uid: UID, qks: QueryKeys) -> bool:
        node_data = self.db.nodes[uid]["data"]
        matches = []
        for qk in qks.all:
            matches.append(getattr(node_data, qk.key) == qk.value)
        # AND matches
        return all(matches)

    def subgraph(self, qks: QueryKeys) -> Any:
        filter_func = partial(self._filter_nodes_by, qks=qks)
        return nx.subgraph_view(self.db, filter_node=filter_func)

    def topological_sort(self, subgraph: Any) -> Any:
        return list(nx.topological_sort(subgraph))

    @staticmethod
    def _load_from_path(file_path: str) -> None:
        with open(file_path, "rb") as f:
            bytes = f.read()
        return _deserialize(blob=bytes, from_bytes=True)

    def exists(self, uid: Any) -> bool:
        return uid in self.nodes()


@serializable()
class InMemoryGraphConfig(StoreConfig):
    store_type: Type[BaseGraphStore] = NetworkXBackingStore
    client_config: StoreClientConfig = InMemoryStoreClientConfig()
    locking_config: LockingConfig = FileLockingConfig()


@serializable()
class ActionGraphStore:
    pass


@serializable()
class InMemoryActionGraphStore(ActionGraphStore):
    def __init__(self, store_config: StoreConfig):
        self.store_config: StoreConfig = store_config
        self.graph: Type[BaseGraphStore] = self.store_config.store_type(
            self.store_config
        )

    def set(
        self,
        node: NodeActionData,
        credentials: SyftVerifyKey,
        parent_uids: List[UID] = [],
    ) -> Result[NodeActionData, str]:
        if self.graph.exists(uid=node.id):
            return Err(f"Node already exists in the graph: {node}")

        # parent_uids = self._search_parents_for(node)
        self.graph.set(uid=node.id, data=node)
        for parent_uid in parent_uids:
            result = self.add_edge(
                parent=parent_uid,
                child=node.id,
                credentials=credentials,
            )
            if result.is_err():
                return result

        try:
            if node.is_mutated:
                # Mutation happens. Update all parents to reflect this.
                for parent_uid in parent_uids:
                    self.update(
                        uid=parent_uid,
                        data=NodeActionDataUpdate(is_mutated=True),
                        credentials=credentials,
                    )
        except Exception:
            pass

        return Ok(node)

    def get(
        self,
        uid: UID,
        credentials: SyftVerifyKey,
    ) -> Result[NodeActionData, str]:
        # 🟡 TODO: Add permission check
        node_data = self.graph.get(uid=uid)
        return Ok(node_data)

    def delete(
        self,
        uid: UID,
        credentials: SyftVerifyKey,
    ) -> Result[bool, str]:
        # 🟡 TODO: Add permission checks
        if self.graph.exists(uid=uid):
            self.graph.delete(uid=uid)
            return Ok(True)
        return Err(f"Node does not exists with id: {uid}")

    def update(
        self,
        uid: UID,
        data: NodeActionDataUpdate,
        credentials: SyftVerifyKey,
    ) -> Result[NodeActionData, str]:
        # 🟡 TODO: Add permission checks
        node_data = self.graph.get(uid=uid)
        if node_data is not None:
            for key, val in data.to_dict(exclude_empty=True).items():
                setattr(node_data, key, val)
            self.graph.update(uid=uid, data=node_data)
            return Ok(node_data)
        return Err(f"Node does not exists for uid: {uid}")

    def _find_mutation_for(self, uid: UID) -> Result[UID, str]:
        def find_non_mutated_successor(uid: UID) -> Optional[UID]:
            """
            Find the leaf node of a mutated chain. This is the node that is not mutated.
            """
            # TODO: Look for a more robust traversal/search method
            node_data = self.graph.get(uid=uid)
            if node_data.is_mutated:
                successor_uids = self.graph.get_successors(uid=uid)
                for successor_uid in successor_uids:
                    # successor_node_data = self.graph.get(uid=successor_uid)
                    result_uid = find_non_mutated_successor(successor_uid)
                    if result_uid is not None:
                        return result_uid
                    else:
                        continue
            else:
                return uid

            return None

        _successor = find_non_mutated_successor(uid=uid)
        if _successor is None:
            return Err(f"Failed to find a non mutated successor for node: {uid}")

        return Ok(_successor)

    def add_edge(
        self,
        parent: UID,
        child: UID,
        credentials: SyftVerifyKey,
    ) -> Result[bool, str]:
        if not self.graph.exists(parent):
            return Err(f"Node does not exists for uid (parent): {parent}")

        if not self.graph.exists(child):
            return Err(f"Node does not exists for uid (child): {child}")

        result = self._find_mutation_for(parent)

        if result.is_err():
            return result

        new_parent = result.ok()

        self.graph.add_edge(parent=new_parent, child=child)

        return Ok(True)

    def _search_parents_for(self, node: NodeActionData) -> Set:
        input_ids = []
        parents = set()
        if node.action.remote_self:
            input_ids.append(node.action.remote_self)
        input_ids.extend(node.action.args)
        input_ids.extend(node.action.kwargs.values())

        # search for parents in the existing nodes
        for uid, _node_data in self.graph.nodes():
            _node = _node_data["data"]
            if _node.action.result_id in input_ids:
                parents.add(uid)

        return parents

    def is_parent(self, parent: UID, child: UID) -> Result[bool, str]:
        if self.graph.exists(child):
            parents = self.graph.get_predecessors(child)
            result = parent in parents
            return Ok(result)
        return Err(f"Node doesn't exists for id: {child}")

    def query(
        self,
        qks: Union[QueryKey, QueryKeys],
        credentials: SyftVerifyKey,
    ) -> Result[List[NodeActionData], str]:
        if isinstance(qks, QueryKey):
            qks = QueryKeys(qks=[qks])
        subgraph = self.graph.subgraph(qks=qks)
        return Ok(self.graph.topological_sort(subgraph=subgraph))

    def nodes(self, credentials: SyftVerifyKey) -> Result[List, str]:
        return Ok(self.graph.nodes())

    def edges(self, credentials: SyftVerifyKey) -> Result[List, str]:
        return Ok(self.graph.edges())
