from supermoto import resources
from moto import mock_dynamodb2, mock_sqs, mock_s3, mock_ecs, mock_ec2

from supermoto.resources import EcsCluster
import boto3


def test_dynamo_table():
    with mock_dynamodb2():
        resources.dynamo_table("hello")


def test_sqs():
    with mock_sqs():
        resources.sqs_queue("helloq")


def test_bucket():
    with mock_s3():
        resources.s3_bucket("abababab")


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
