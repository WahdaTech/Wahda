#!/bin/bash
set -euxo pipefail

WORKDIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$WORKDIR"
REPO_ROOT=$( git rev-parse --show-toplevel )
CONTRIB_PATH="$REPO_ROOT/contrib"

python -m grpc_tools.protoc \
    --python_out=. \
    --mypy_out=. \
    --grpc_python_out=. \
    --mypy_grpc_out=. \
    -I="$CONTRIB_PATH/etcd-io" \
    -I="$CONTRIB_PATH/gogo/protobuf" \
    -I="$CONTRIB_PATH/googleapis/googleapis" \
    "$CONTRIB_PATH/etcd-io/etcd/api/authpb/auth.proto" \
    "$CONTRIB_PATH/etcd-io/etcd/api/etcdserverpb/rpc.proto" \
    "$CONTRIB_PATH/etcd-io/etcd/api/mvccpb/kv.proto" \
    "$CONTRIB_PATH/gogo/protobuf/gogoproto/gogo.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/annotations.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/auth.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/backend.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/billing.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/client.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/config_change.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/consumer.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/context.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/control.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/distribution.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/documentation.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/endpoint.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/error_reason.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/field_behavior.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/field_info.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/http.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/httpbody.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/label.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/launch_stage.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/log.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/logging.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/metric.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/monitored_resource.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/monitoring.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/policy.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/quota.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/resource.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/routing.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/service.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/source_info.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/system_parameter.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/usage.proto" \
    "$CONTRIB_PATH/googleapis/googleapis/google/api/visibility.proto"

# shellcheck disable=SC2046
sed -i 's|etcd.api|proto.etcd.api|g' $(find ./etcd/api/ -type f -name '*.pyi')
# shellcheck disable=SC2046
sed -i 's|google.api|proto.google.api|g' $(find ./google/api/ -type f -name '*.pyi')
