from supermoto import resources
from moto import mock_dynamodb2, mock_sqs, mock_s3, mock_ecs, mock_ec2

from supermoto.resources import EcsCluster, IndexSpec
import boto3
from typing import List, Dict, Any, Tuple

TEST_BUCKET = "bukeet"


def key_adder(rules: List[Tuple[str, List[str]]]):
    def addkeys(d: Dict[str, Any]):
        for rulek, rulefields in rules:
            parts = []
            for field in rulefields:

                parts.append(field.upper())
                parts.append(str(d[field]))

            d[rulek] = "#".join(parts)

    return addkeys


def test_dynamo_table():
    with mock_dynamodb2():
        putter = resources.dynamo_table("hello")

        putter({
            "id": "oneid",
            "a": "1"
        })
        dump = resources.dynamo_dump("hello")
        assert dump == [{'a': {'S': '1'}, 'id': {'S': 'oneid'}}]

        putter = resources.dynamo_table("withindex", "pk", "sk", False, indexes=[
            IndexSpec(name="Index1", pk="GSI1PK", sk="GSI1SK"),
            IndexSpec(name="Index2", pk="GSI2PK", sk="GSI2SK")
        ])

        add_keys = key_adder([
            ("pk", ["a"]),
            ("sk", ["a", "b"]),
            ("GSI1PK", ["b"]),
            ("GSI1SK", ["a"])
        ])
        to_add = {
            "a": 1,
            "b": 2
        }

        add_keys(to_add)

        putter(to_add)
        idump = resources.dynamo_index_dump("withindex", "Index1")
        assert idump == [{'GSI1PK': {'S': 'B#2'},  'GSI1SK': {'S': 'A#1'},
                          'a': {'N': '1'},  'b': {'N': '2'},  'pk': {'S': 'A#1'},  'sk': {'S': 'A#1#B#2'}}]
        print(idump)


def test_sqs():
    with mock_sqs():
        resources.sqs_queue("helloq")


def test_bucket():
    with mock_s3():
        put = resources.s3_bucket(TEST_BUCKET)
        put("a/1", b"one")
        put("a/2", b"two")
        put("b/3", b"three")

        ls = resources.s3_ls(TEST_BUCKET)
        assert ls == ['a/1', 'a/2', 'b/3']

        lsb = resources.s3_get_objects(TEST_BUCKET, "b")
        assert lsb == {'b/3': b'three'}

        all_objects = resources.s3_get_objects(TEST_BUCKET)
        assert all_objects == {'a/1': b'one', 'a/2': b'two', 'b/3': b'three'}


def test_ecs():
    cl = EcsCluster(
        cluster_name="name",
        task_definitions=["one", "two"]
    )
    with mock_ecs(), mock_ec2():
        resources.ecs_cluster(cl)
        ecs = boto3.client("ecs")
        ran = ecs.run_task(cluster=cl.cluster_name,
                           taskDefinition=cl.task_definitions[0]
                           )
        print(ran)
