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

        fdao.add(FooModel(k1="a1", date="a1", username="tauno"))
        fdao.add(FooModel(k1="a1", date="b1", username="tauno"))


        # returns both MyModel and FooModel items
        pkrows = fdao.query_pk(FooKey(k1="a1"))
        assert len(pkrows) == 4
        pprint(pkrows)


        # returns only FooModel items (because of !Foo in SK rules)
        skrows = fdao.query_beg(FooKey(k1="a1"))
        assert len(skrows) == 2


        # gets only 'b' row
        sk2rows = fdao.query_beg(FooKey(k1="a1", date="b"))
        assert len(sk2rows) == 1
        def beg_create(k, val):
            return k.begins_with(val)

        sk3rows = fdao.query_cond(FooKey(k1="a1", date="a"), beg_create)
        print(sk3rows)
        assert len(sk3rows) == 1
        assert sk3rows[0]["date"] == "a1"
