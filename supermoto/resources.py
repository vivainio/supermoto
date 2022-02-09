import json
from dataclasses import dataclass, field
from typing import List, Callable, Any, Dict, Optional

import boto3

from .helpers import generate_instance_identity_document


@dataclass
class EcsCluster:
    cluster_name: str
    task_definitions: List[str]


_dynamo_endpoint = None


def set_dynamo_endpoint_url(endpoint_url: Optional[str]):
    """ use this to override endpoint, e.g. to local simulator """
    global _dynamo_endpoint
    _dynamo_endpoint = endpoint_url


def dynamo_client() -> boto3.client:
    """ overwrite this e.g. if you want to use local endpoint """
    if _dynamo_endpoint:
        return boto3.client("dynamodb", endpoint_url=_dynamo_endpoint)
    return boto3.client("dynamodb")


def dynamo_resource() -> boto3.resource:
    """ overwrite this e.g. if you want to use local endpoint """
    if _dynamo_endpoint:
        return boto3.resource("dynamodb", endpoint_url=_dynamo_endpoint)

    return boto3.resource("dynamodb")


@dataclass
class IndexSpec:
    name: str
    pk: str = "GSI1PK"
    sk: str = "GSI1SK"
    projection: Dict[str, Any] = field(default_factory=lambda: {"ProjectionType": "ALL"})


def dynamo_table(table_name: str, id_attribute: str = "id", range_attribute=None, delete=False,
                 indexes: List[IndexSpec] = []):
    ddb = dynamo_resource()
    client = dynamo_client()

    attrdefs = [{"AttributeName": id_attribute, "AttributeType": "S"}]
    keyschema = [{"AttributeName": id_attribute, "KeyType": "HASH"}]

    if range_attribute is not None:
        attrdefs.append({
            "AttributeName": range_attribute, "AttributeType": "S"
        })
        keyschema.append({
            "AttributeName": range_attribute, "KeyType": "RANGE"
        })
    table = ddb.Table(table_name)

    if delete:
        try:
            table.delete()
        except client.exceptions.ResourceNotFoundException:
            ...

    kwargs = {}

    def gsi(i: IndexSpec):
        def keyschema(name: str, keytype: str):
            return {
                "AttributeName": name,
                "KeyType": keytype
            }

        return {
            "IndexName": i.name,
            "KeySchema": [
                keyschema(i.pk, "HASH"),
                keyschema(i.sk, "RANGE")
            ],
            "Projection": i.projection
        }

    if indexes:
        kwargs["GlobalSecondaryIndexes"] = [
            gsi(i) for i in indexes
        ]
        for idx in indexes:
            attrdefs.extend([{
                "AttributeName": idx.pk,
                "AttributeType": "S"
            }, {
                "AttributeName": idx.sk,
                "AttributeType": "S"
            }])


    ddb.create_table(
        AttributeDefinitions=attrdefs,
        TableName=table_name,
        KeySchema=keyschema,
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        **kwargs
    )

    def put_item(ent):
        table.put_item(Item=ent)

    return put_item


def dynamo_dump(table_name: str):
    ddb = dynamo_client()
    r = ddb.scan(TableName=table_name)
    return r["Items"]


def dynamo_index_dump(table_name: str, index_name: str):
    ddb = dynamo_client()
    r = ddb.scan(TableName=table_name, IndexName=index_name)
    return r["Items"]


def dynamo_ls() -> List[str]:
    ddb = dynamo_client()
    return ddb.list_tables()["TableNames"]


def sqs_queue(queue_name: str) -> Callable[[Any], None]:
    """ creates queue, returns function that can be used to send messages """
    sqs = boto3.client("sqs")
    create_resp = sqs.create_queue(QueueName=queue_name)
    qurl = create_resp["QueueUrl"]

    def sqs_sender(msg):
        sqs.send_message(QueueUrl=qurl, MessageBody=msg)

    return sqs_sender


def s3_bucket(bucket_name: str) -> Callable[[str, bytes], None]:
    """ returns function you can use to populate initial stuff to bucket """
    client = boto3.client("s3", region_name="eu-west-1")
    client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )

    def s3_put(key: str, cont: bytes) -> None:
        client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=cont
        )

    return s3_put


def s3_ls(bucket_name: str) -> List[str]:
    """ list all files in the bucket """
    client = boto3.client("s3", region_name="eu-west-1")
    resp = client.list_objects(Bucket=bucket_name)
    return [ent["Key"] for ent in resp["Contents"]]


def s3_get_objects(bucket_name: str, prefix: str = None) -> Dict[str, bytes]:
    """ load all files in the bucket to dict"""
    client = boto3.client("s3", region_name="eu-west-1")
    if prefix:
        resp = client.list_objects(Bucket=bucket_name, Prefix=prefix)
    else:
        resp = client.list_objects(Bucket=bucket_name)
    objects = [ent["Key"] for ent in resp["Contents"]]

    res = {}
    for o in objects:
        cont = client.get_object(Bucket=bucket_name, Key=o)
        res[o] = cont["Body"].read()
    return res


def s3_clear(bucket_name: str):
    items = s3_ls(bucket_name)
    client = boto3.client("s3", region_name="eu-west-1")
    to_delete = [
        {
            "Key": key
        } for key in items
    ]
    client.delete_objects(
        Bucket=bucket_name,
        Delete={
            "Objects": to_delete
        }
    )


def sns_topic(topic_name: str) -> str:
    """ returns arn that you need to use for publishing """
    client = boto3.client("sns", region_name="eu-west-1")
    created = client.create_topic(Name=topic_name)
    return created["TopicArn"]


def ecs_ls(cluster_name: str, desired_status="RUNNING"):
    """ List (and describes) all the tasks running in ECS cluster, with specified status """
    client = boto3.client("ecs", region_name="eu-west-1")
    tasks = client.list_tasks(cluster=cluster_name, desiredStatus=desired_status)
    if not tasks:
        return []

    arns = tasks.get("taskArns", [])
    if not arns:
        return []

    describe = client.describe_tasks(
        cluster=cluster_name,
        tasks=arns,
        include=["TAGS"]
    )
    return describe["tasks"]


def ecs_cluster(definition: EcsCluster):
    """ Creates ecs cluster """
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
