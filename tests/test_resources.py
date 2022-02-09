from supermoto import resources
from moto import mock_dynamodb2, mock_sqs, mock_s3, mock_ecs, mock_ec2

from supermoto.resources import EcsCluster, IndexSpec
import boto3

TEST_BUCKET = "bukeet"



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

        to_add = {
            "pk": "pk",
            "sk": "sk",
            "GSI1PK": "ipk",
            "GSI1SK": "ipk",
            "GSI2PK": "ipk2",
            "GSI2SK": "ipk2",
            "a": 1,
            "b": 2
        }

        putter(to_add)
        idump = resources.dynamo_index_dump("withindex", "Index1")
        assert idump == [{'pk': {'S': 'pk'}, 'sk': {'S': 'sk'}, 'GSI1PK': {'S': 'ipk'}, 'GSI1SK': {'S': 'ipk'}, 'GSI2PK': {'S': 'ipk2'}, 'GSI2SK': {'S': 'ipk2'}, 'a': {'N': '1'}, 'b': {'N': '2'}}]
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


