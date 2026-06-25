# supermoto

Thin helpers for creating AWS resources when authoring [`moto`](https://github.com/getmoto/moto) test cases (and other AWS test setup).

`moto` mocks AWS, but you still have to write a lot of boilerplate `boto3` calls to stand up the tables, queues and buckets your code under test expects. `supermoto` wraps the common cases in one-liners that return small "do something to this resource" closures, so test setup stays short.

[API documentation](https://vivainio.github.io/supermoto/)

## Install

```bash
pip install supermoto
```

`boto3` and `moto` are not pinned as dependencies — install the versions your project uses.

## Quick start

```python
from moto import mock_dynamodb2, mock_s3
from supermoto import resources

def test_something():
    with mock_dynamodb2():
        put = resources.dynamo_table("my-table")      # creates table, returns a putter
        put({"id": "abc", "name": "thing"})            # add a seed row
        rows = resources.dynamo_dump("my-table")       # read it all back

    with mock_s3():
        put_obj = resources.s3_bucket("my-bucket")     # creates bucket, returns a putter
        put_obj("path/to/key", b"contents")
        keys = resources.s3_ls("my-bucket")
```

Most "create" helpers follow the same pattern: they create the resource and **return a callable** you use to populate it.

## API

All functions live in `supermoto.resources`.

### DynamoDB

```python
dynamo_table(table_name, id_attribute="id", range_attribute=None,
             delete=False, indexes=[]) -> put_item
```
Create a table and return a `put_item(item: dict)` function.
- `id_attribute` — partition (HASH) key name, type string.
- `range_attribute` — optional sort (RANGE) key name, type string.
- `delete=True` — delete the table first if it already exists (ignores "not found").
- `indexes` — list of `IndexSpec` for global secondary indexes.

```python
from supermoto.resources import IndexSpec

put = dynamo_table("t", "pk", "sk", indexes=[
    IndexSpec(name="Index1", pk="GSI1PK", sk="GSI1SK"),
    IndexSpec(name="Index2", pk="GSI2PK", sk="GSI2SK"),
])
```

`IndexSpec(name, pk="GSI1PK", sk="GSI1SK", projection={"ProjectionType": "ALL"})`
describes one GSI. Its `pk`/`sk` attributes are added to the table's attribute
definitions automatically (string typed).

Other DynamoDB helpers:

| Function | Returns |
| --- | --- |
| `dynamo_dump(table_name)` | all items via `scan` (raw DynamoDB JSON, e.g. `{"id": {"S": "x"}}`) |
| `dynamo_index_dump(table_name, index_name)` | all items scanned through a named index |
| `dynamo_ls()` | list of table names |

Endpoint override (e.g. to point at a local DynamoDB instead of `moto`):

```python
resources.set_dynamo_endpoint_url("http://localhost:8000")  # None to reset
```
`dynamo_client()` / `dynamo_resource()` honor this override and are used by all the helpers above.

### SQS

```python
send = sqs_queue("my-queue")   # creates queue, returns sender
send("a message body")
```

### S3

```python
put = s3_bucket("my-bucket")          # creates bucket (region eu-west-1), returns putter
put("key", b"bytes")

s3_ls("my-bucket")                    # -> list of keys
s3_get_objects("my-bucket")           # -> {key: bytes} for every object
s3_get_objects("my-bucket", "prefix") # -> {key: bytes} filtered by prefix
s3_clear("my-bucket")                 # delete every object in the bucket
```

### SNS

```python
arn = sns_topic("my-topic")   # creates topic, returns its ARN for publishing
```

### ECS

```python
from supermoto.resources import EcsCluster

ecs_cluster(EcsCluster(cluster_name="name", task_definitions=["one", "two"]))
ecs_ls("name")                       # list + describe tasks (desired_status="RUNNING")
ecs_ls("name", desired_status="STOPPED")
```
`ecs_cluster` creates the cluster, registers each task definition, spins up a test
EC2 instance and registers it as a container instance (so `run_task` works under
`moto`). Requires both `mock_ecs()` and `mock_ec2()`.

> Note: S3/SNS/ECS helpers hardcode region `eu-west-1`.

## Development

This repo uses a tiny `tasks.py` runner:

```bash
py tasks.py test     # run pytest (from tests/)
py tasks.py check    # mypy
py tasks.py black    # format
py tasks.py docs     # regenerate HTML docs with pdoc3
py tasks.py publish  # build sdist + twine upload
```

## License

MIT — see [LICENSE](LICENSE).
