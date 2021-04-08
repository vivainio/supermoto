import json
from dataclasses import dataclass
from typing import List

import boto3

from .helpers import generate_instance_identity_document


@dataclass
class EcsCluster:
    cluster_name: str
    task_definitions: List[str]


def dynamo_table(table_name: str, id_attribute: str = "id", range_attribute = None):
    ddb = boto3.client("dynamodb")

    attrdefs = [{"AttributeName": id_attribute, "AttributeType": "S"}]
    keyschema = [{"AttributeName": id_attribute, "KeyType": "HASH"}]

    if range_attribute is not None:
        attrdefs.append({
            "AttributeName": range_attribute, "AttributeType": "S"
        })
        keyschema.append({
            "AttributeName": range_attribute, "KeyType": "RANGE"
        })

    ddb.create_table(
        AttributeDefinitions= attrdefs,
        TableName=table_name,
        KeySchema= keyschema,
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

def s3_ls(bucket_name: str) -> List[str]:
    """ list all files in the bucket """
    client = boto3.client("s3", region_name="eu-west-1")
    resp = client.list_objects(Bucket=bucket_name)
    return [ent["Key"] for ent in resp["Contents"]]



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
