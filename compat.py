"""
Stub broken opentelemetry gRPC/protobuf modules before chromadb imports them.
These modules use C-extension protobuf generated files that crash on Python 3.14.
chromadb only needs them for optional telemetry export — stubbing them is safe.
"""
import os
import sys
from unittest.mock import MagicMock

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_ANONYMIZED_TELEMETRY", "False")

_BROKEN = [
    "opentelemetry.proto",
    "opentelemetry.proto.common",
    "opentelemetry.proto.common.v1",
    "opentelemetry.proto.common.v1.common_pb2",
    "opentelemetry.proto.trace",
    "opentelemetry.proto.trace.v1",
    "opentelemetry.proto.trace.v1.trace_pb2",
    "opentelemetry.proto.resource",
    "opentelemetry.proto.resource.v1",
    "opentelemetry.proto.resource.v1.resource_pb2",
    "opentelemetry.proto.collector",
    "opentelemetry.proto.collector.trace",
    "opentelemetry.proto.collector.trace.v1",
    "opentelemetry.proto.collector.trace.v1.trace_service_pb2",
    "opentelemetry.exporter.otlp.proto",
    "opentelemetry.exporter.otlp.proto.grpc",
    "opentelemetry.exporter.otlp.proto.grpc.exporter",
    "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
]
for _mod in _BROKEN:
    sys.modules.setdefault(_mod, MagicMock())
