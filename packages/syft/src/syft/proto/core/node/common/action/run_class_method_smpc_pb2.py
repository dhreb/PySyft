# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proto/core/node/common/action/run_class_method_smpc.proto
"""Generated protocol buffer code."""
# third party
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


# syft absolute
from syft.proto.core.common import (
    common_object_pb2 as proto_dot_core_dot_common_dot_common__object__pb2,
)
from syft.proto.core.io import address_pb2 as proto_dot_core_dot_io_dot_address__pb2
from syft.proto.core.pointer import (
    pointer_pb2 as proto_dot_core_dot_pointer_dot_pointer__pb2,
)

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n9proto/core/node/common/action/run_class_method_smpc.proto\x12\x1csyft.core.node.common.action\x1a%proto/core/common/common_object.proto\x1a proto/core/pointer/pointer.proto\x1a\x1bproto/core/io/address.proto"\xb5\x03\n\x18RunClassMethodSMPCAction\x12\x0c\n\x04path\x18\x01 \x01(\t\x12)\n\x05_self\x18\x02 \x01(\x0b\x32\x1a.syft.core.pointer.Pointer\x12(\n\x04\x61rgs\x18\x03 \x03(\x0b\x32\x1a.syft.core.pointer.Pointer\x12R\n\x06kwargs\x18\x04 \x03(\x0b\x32\x42.syft.core.node.common.action.RunClassMethodSMPCAction.KwargsEntry\x12-\n\x0eid_at_location\x18\x05 \x01(\x0b\x32\x15.syft.core.common.UID\x12\x19\n\x11seed_id_locations\x18\x06 \x01(\t\x12&\n\x07\x61\x64\x64ress\x18\x07 \x01(\x0b\x32\x15.syft.core.io.Address\x12%\n\x06msg_id\x18\x08 \x01(\x0b\x32\x15.syft.core.common.UID\x1aI\n\x0bKwargsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12)\n\x05value\x18\x02 \x01(\x0b\x32\x1a.syft.core.pointer.Pointer:\x02\x38\x01\x62\x06proto3'
)


_RUNCLASSMETHODSMPCACTION = DESCRIPTOR.message_types_by_name["RunClassMethodSMPCAction"]
_RUNCLASSMETHODSMPCACTION_KWARGSENTRY = _RUNCLASSMETHODSMPCACTION.nested_types_by_name[
    "KwargsEntry"
]
RunClassMethodSMPCAction = _reflection.GeneratedProtocolMessageType(
    "RunClassMethodSMPCAction",
    (_message.Message,),
    {
        "KwargsEntry": _reflection.GeneratedProtocolMessageType(
            "KwargsEntry",
            (_message.Message,),
            {
                "DESCRIPTOR": _RUNCLASSMETHODSMPCACTION_KWARGSENTRY,
                "__module__": "proto.core.node.common.action.run_class_method_smpc_pb2"
                # @@protoc_insertion_point(class_scope:syft.core.node.common.action.RunClassMethodSMPCAction.KwargsEntry)
            },
        ),
        "DESCRIPTOR": _RUNCLASSMETHODSMPCACTION,
        "__module__": "proto.core.node.common.action.run_class_method_smpc_pb2"
        # @@protoc_insertion_point(class_scope:syft.core.node.common.action.RunClassMethodSMPCAction)
    },
)
_sym_db.RegisterMessage(RunClassMethodSMPCAction)
_sym_db.RegisterMessage(RunClassMethodSMPCAction.KwargsEntry)

if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _RUNCLASSMETHODSMPCACTION_KWARGSENTRY._options = None
    _RUNCLASSMETHODSMPCACTION_KWARGSENTRY._serialized_options = b"8\001"
    _RUNCLASSMETHODSMPCACTION._serialized_start = 194
    _RUNCLASSMETHODSMPCACTION._serialized_end = 631
    _RUNCLASSMETHODSMPCACTION_KWARGSENTRY._serialized_start = 558
    _RUNCLASSMETHODSMPCACTION_KWARGSENTRY._serialized_end = 631
# @@protoc_insertion_point(module_scope)
