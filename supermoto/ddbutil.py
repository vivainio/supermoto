from typing import List, Dict, Any, Tuple, Optional, Generic, TypeVar, Callable

from dataclasses import dataclass

import boto3
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
from boto3.dynamodb.conditions import Key, AttributeBase

_serializer = TypeSerializer()
_deserializer = TypeDeserializer()


def serialize(obj: Dict[str, Any]):
    return _serializer.serialize(obj)["M"]


def deserialize(obj: Dict[str, Any]):
    return _deserializer.deserialize({"M": obj})


@dataclass()
class KeygenRules:
    pk: List[str]
    sk: List[str]
    extra: Optional[Dict[str, Any]] = None

    # cols: List[Tuple[str, List[str]]]


def generate_keys_with_rules(rules: List[Any], d: Dict[str, Any]):
    resp = {}
    for rulek, rulefields in rules:
        parts = []

        for field in rulefields:
            if field.startswith("!"):
                parts.append(field[1:])
                continue

            val = d[field]
            # first None stops key generation. use for begins_with etc
            if val is None:
                break
            parts.append(field)
            parts.append(str(val))

        resp[rulek] = "#".join(parts)
    return resp


def key_adder(rules: KeygenRules, fixed: Dict[str, Any] = {}):
    # simple fo
    def addkeys(d: Dict[str, Any]):
        # add fixed items first so they can be used in keys
        d.update(fixed)
        generate_keys_with_rules(rules, d)

    return addkeys


TKey = TypeVar("TKey")
TVal = TypeVar("TVal")


def ddb_client() -> boto3.client:
    return boto3.client("dynamodb")


def ddb_table(tablename: str) -> Any:
    return boto3.resource("dynamodb").Table(tablename)


@dataclass()
class TableSpec:
    name: str
    pk: str = "PK"
    sk: str = "SK"
    type_col: Optional[str] = None


# first rule is always pk rule, then sk rule
def parse_rules(db: TableSpec, rules: KeygenRules):
    return [(db.pk, rules.pk), (db.sk, rules.sk)]


class Dao(Generic[TKey, TVal]):
    def __init__(self, keyclass: TKey, valclass: TVal, spec: TableSpec):
        self.rules = parse_rules(spec, valclass.get_key_cols())

        # self.rules = #valclass.get_key_cols()
        # self.keyclass = keyclass
        self.valclass = valclass
        self.spec = spec
        self.key_adder = key_adder(self.rules)

    def _table(self):
        return ddb_table(self.spec.name)

    def add(self, obj: TVal):
        d = obj.dict()
        keys = generate_keys_with_rules(self.rules, d)
        d.update(keys)
        if self.spec.type_col:
            d[self.spec.type_col] = type(obj).__name__
        self._table().put_item(Item=d)

    def get(self, key: TKey) -> Optional[TVal]:
        keyd = key.dict()
        key = generate_keys_with_rules(self.rules, keyd)
        got = self._table().get_item(Key=key).get("Item")
        if got is None:
            return None
        return self.valclass(**got)


    def query_pk(self, key: TKey):
        # this will stop at first None
        pkval = generate_keys_with_rules([self.rules[0]], key.dict())[self.spec.pk]
        got = self._table().query(
            KeyConditionExpression=Key(self.spec.pk).eq(pkval))

        return got

    def query_beg(self, key: TKey):
        return self.query_cond(key, lambda key, val: key.begins_with(val))

    def query_cond(self, key: TKey, cond_function: Callable[[Key, str], Any]):

        # can write more complex queries using both pk and sk
        keyd = key.dict()
        pkval = generate_keys_with_rules([self.rules[0]], keyd)[self.spec.pk]
        skval = generate_keys_with_rules([self.rules[1]], keyd)[self.spec.sk]

        other_cond = cond_function(Key(self.spec.sk), skval)
        print(other_cond)
        return self._table().query(
            KeyConditionExpression=Key(self.spec.pk).eq(pkval) & other_cond )

