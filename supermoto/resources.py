import json
from dataclasses import dataclass
from typing import List

import boto3

from .helpers import generate_instance_identity_document


@dataclass
class EcsCluster:
    cluster_name: str
    task_definitions: List[str]


def dynamo_table(table_name: str, id_attribute: str = "id"):
    ddb = boto3.client("dynamodb")
    ddb.create_table(
        AttributeDefinitions=[{"AttributeName": id_attribute, "AttributeType": "S"}],
        TableName=table_name,
        KeySchema=[{"AttributeName": id_attribute, "KeyType": "HASH"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )


def sqs_queue(queue_name: str, initial_message=None):
    sqs = boto3.client("sqs")
    sqs.create_queue(QueueName=queue_name)
    if initial_message:
        sqs.send_message(QueueUrl=queue_name, MessageBody=initial_message)


def s3_bucket(bucket_name: str):
    client = boto3.client("s3", region_name="eu-west-1")
    client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )


def ecs_cluster(definition: EcsCluster):
    client = boto3.client("ecs", region_name="eu-west-1")
    ec2 = boto3.resource("ec2", region_name="eu-west-1")
    client.create_cluster(clusterName=definition.cluster_name)
    for td in definition.task_definitions:
        client.register_task_definition(
            family=td,
            containerDefinitions=[
                {
                    "name": "supermoto-taskdef-" + td,
                    "memory": 400,
                    "essential": True,
                    "environment": [
                        {"name": "AWS_ACCESS_KEY_ID", "value": "SOME_ACCESS_KEY"}
                    ],
                    "logConfiguration": {"logDriver": "json-file"},
                }
            ],
        )

    test_instance = ec2.create_instances(
        # EXAMPLE_AMI_ID from Moto
        ImageId="ami-12c6146b",
        MinCount=1,
        MaxCount=1,
    )[0]

    instance_id_document = json.dumps(
        generate_instance_identity_document(test_instance)
    )

    client.register_container_instance(
        cluster=definition.cluster_name, instanceIdentityDocument=instance_id_document
    )
