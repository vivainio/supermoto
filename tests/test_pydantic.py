from pprint import pprint
from typing import Any, Callable, Generic, TypeVar, List, Tuple, Type, Optional

from moto import mock_dynamodb2
from pydantic import BaseModel

from supermoto import resources
from supermoto.ddbutil import key_adder, generate_keys_with_rules, KeygenRules, Dao, TableSpec


# key is used for GET
# start with mandatory pk values. then follow with optional sk values. first None cuts the query
class MyKey(BaseModel):
    k1: str
    k2: str
    k3: Optional[str]

    @staticmethod
    def get_key_cols() -> KeygenRules:
        # on prefix !, emit the name verbatim witout any value lookup, e.g. MYKEY#k1#k1value
        return KeygenRules(pk = ["k1"], sk=["!MYKEY", "k2", "k1"])


class MyModel(MyKey):
    a: str
    b: int


class FooKey(BaseModel):
    k1: str
    date: Optional[str]
    @staticmethod
    def get_key_cols() -> KeygenRules:
        return KeygenRules(pk= ["k1"], sk = ["!Foo", "date"])

class FooModel(FooKey):
    username: str


def test_serialize_model():
    with mock_dynamodb2():
        resources.dynamo_table("mytable", "pk", "sk")
        db = TableSpec(name="mytable", pk="pk", sk="sk", type_col="type")
        dao = Dao(MyKey, MyModel, db)

        m = MyModel(k1="a1", k2="a2", a="aval", b=12)
        dao.add(m)

        g = dao.get(MyKey(k1="a1", k2="a2"))
        print(g)

        fdao = Dao(FooKey, FooModel, db)

        f = FooModel(k1="a1", date="12222", username="tauno")
        fdao.add(f)


        pkrows = fdao.query_pk(FooKey(k1="a1"))
        pprint(pkrows)

        skrows = fdao.query_beg(FooKey(k1="a1"))
        pprint(skrows)

        def beg_create(k, val):
            print(k,val)
            return k.begins_with(val)

        other_skrows = fdao.query_cond(FooKey(k1="a1"), beg_create)
        pprint(other_skrows)

        assert skrows["Items"] == other_skrows["Items"]
        #assert skrows == other_skrows