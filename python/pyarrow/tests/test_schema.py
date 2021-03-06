# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import pickle

import pytest
import numpy as np

import pyarrow as pa


def test_type_integers():
    dtypes = ['int8', 'int16', 'int32', 'int64',
              'uint8', 'uint16', 'uint32', 'uint64']

    for name in dtypes:
        factory = getattr(pa, name)
        t = factory()
        assert str(t) == name


def test_type_to_pandas_dtype():
    M8_ns = np.dtype('datetime64[ns]')
    cases = [
        (pa.null(), np.float64),
        (pa.bool_(), np.bool_),
        (pa.int8(), np.int8),
        (pa.int16(), np.int16),
        (pa.int32(), np.int32),
        (pa.int64(), np.int64),
        (pa.uint8(), np.uint8),
        (pa.uint16(), np.uint16),
        (pa.uint32(), np.uint32),
        (pa.uint64(), np.uint64),
        (pa.float16(), np.float16),
        (pa.float32(), np.float32),
        (pa.float64(), np.float64),
        (pa.date32(), M8_ns),
        (pa.date64(), M8_ns),
        (pa.timestamp('ms'), M8_ns),
        (pa.binary(), np.object_),
        (pa.binary(12), np.object_),
        (pa.string(), np.object_),
        (pa.list_(pa.int8()), np.object_),
    ]
    for arrow_type, numpy_type in cases:
        assert arrow_type.to_pandas_dtype() == numpy_type


def test_type_list():
    value_type = pa.int32()
    list_type = pa.list_(value_type)
    assert str(list_type) == 'list<item: int32>'

    field = pa.field('my_item', pa.string())
    l2 = pa.list_(field)
    assert str(l2) == 'list<my_item: string>'


def test_type_comparisons():
    val = pa.int32()
    assert val == pa.int32()
    assert val == 'int32'

    with pytest.raises(TypeError):
        val == 5


def test_type_for_alias():
    cases = [
        ('i1', pa.int8()),
        ('int8', pa.int8()),
        ('i2', pa.int16()),
        ('int16', pa.int16()),
        ('i4', pa.int32()),
        ('int32', pa.int32()),
        ('i8', pa.int64()),
        ('int64', pa.int64()),
        ('u1', pa.uint8()),
        ('uint8', pa.uint8()),
        ('u2', pa.uint16()),
        ('uint16', pa.uint16()),
        ('u4', pa.uint32()),
        ('uint32', pa.uint32()),
        ('u8', pa.uint64()),
        ('uint64', pa.uint64()),
        ('f4', pa.float32()),
        ('float32', pa.float32()),
        ('f8', pa.float64()),
        ('float64', pa.float64()),
        ('date32', pa.date32()),
        ('date64', pa.date64()),
        ('string', pa.string()),
        ('str', pa.string()),
        ('binary', pa.binary()),
        ('time32[s]', pa.time32('s')),
        ('time32[ms]', pa.time32('ms')),
        ('time64[us]', pa.time64('us')),
        ('time64[ns]', pa.time64('ns')),
        ('timestamp[s]', pa.timestamp('s')),
        ('timestamp[ms]', pa.timestamp('ms')),
        ('timestamp[us]', pa.timestamp('us')),
        ('timestamp[ns]', pa.timestamp('ns')),
    ]

    for val, expected in cases:
        assert pa.type_for_alias(val) == expected


def test_type_string():
    t = pa.string()
    assert str(t) == 'string'


def test_type_timestamp_with_tz():
    tz = 'America/Los_Angeles'
    t = pa.timestamp('ns', tz=tz)
    assert t.unit == 'ns'
    assert t.tz == tz


def test_time_types():
    t1 = pa.time32('s')
    t2 = pa.time32('ms')
    t3 = pa.time64('us')
    t4 = pa.time64('ns')

    assert t1.unit == 's'
    assert t2.unit == 'ms'
    assert t3.unit == 'us'
    assert t4.unit == 'ns'

    assert str(t1) == 'time32[s]'
    assert str(t4) == 'time64[ns]'

    with pytest.raises(ValueError):
        pa.time32('us')

    with pytest.raises(ValueError):
        pa.time64('s')


def test_type_from_numpy_dtype_timestamps():
    cases = [
        (np.dtype('datetime64[s]'), pa.timestamp('s')),
        (np.dtype('datetime64[ms]'), pa.timestamp('ms')),
        (np.dtype('datetime64[us]'), pa.timestamp('us')),
        (np.dtype('datetime64[ns]'), pa.timestamp('ns'))
    ]

    for dt, pt in cases:
        result = pa.from_numpy_dtype(dt)
        assert result == pt


def test_field():
    t = pa.string()
    f = pa.field('foo', t)

    assert f.name == 'foo'
    assert f.nullable
    assert f.type is t
    assert repr(f) == "pyarrow.Field<foo: string>"

    f = pa.field('foo', t, False)
    assert not f.nullable


def test_schema():
    fields = [
        pa.field('foo', pa.int32()),
        pa.field('bar', pa.string()),
        pa.field('baz', pa.list_(pa.int8()))
    ]
    sch = pa.schema(fields)

    assert sch.names == ['foo', 'bar', 'baz']

    assert len(sch) == 3
    assert sch[0].name == 'foo'
    assert sch[0].type == fields[0].type
    assert sch.field_by_name('foo').name == 'foo'
    assert sch.field_by_name('foo').type == fields[0].type

    assert repr(sch) == """\
foo: int32
bar: string
baz: list<item: int8>
  child 0, item: int8"""


def test_field_empty():
    f = pa.Field()
    with pytest.raises(ReferenceError):
        repr(f)


def test_field_add_remove_metadata():
    f0 = pa.field('foo', pa.int32())

    assert f0.metadata is None

    metadata = {b'foo': b'bar', b'pandas': b'badger'}

    f1 = f0.add_metadata(metadata)
    assert f1.metadata == metadata

    f3 = f1.remove_metadata()
    assert f3.metadata is None

    # idempotent
    f4 = f3.remove_metadata()
    assert f4.metadata is None

    f5 = pa.field('foo', pa.int32(), True, metadata)
    f6 = f0.add_metadata(metadata)
    assert f5.equals(f6)


def test_schema_add_remove_metadata():
    fields = [
        pa.field('foo', pa.int32()),
        pa.field('bar', pa.string()),
        pa.field('baz', pa.list_(pa.int8()))
    ]

    s1 = pa.schema(fields)

    assert s1.metadata is None

    metadata = {b'foo': b'bar', b'pandas': b'badger'}

    s2 = s1.add_metadata(metadata)
    assert s2.metadata == metadata

    s3 = s2.remove_metadata()
    assert s3.metadata is None

    # idempotent
    s4 = s3.remove_metadata()
    assert s4.metadata is None


def test_schema_equals():
    fields = [
        pa.field('foo', pa.int32()),
        pa.field('bar', pa.string()),
        pa.field('baz', pa.list_(pa.int8()))
    ]

    sch1 = pa.schema(fields)
    sch2 = pa.schema(fields)
    assert sch1.equals(sch2)

    del fields[-1]
    sch3 = pa.schema(fields)
    assert not sch1.equals(sch3)


def test_schema_negative_indexing():
    fields = [
        pa.field('foo', pa.int32()),
        pa.field('bar', pa.string()),
        pa.field('baz', pa.list_(pa.int8()))
    ]

    schema = pa.schema(fields)

    assert schema[-1].equals(schema[2])
    assert schema[-2].equals(schema[1])
    assert schema[-3].equals(schema[0])

    with pytest.raises(IndexError):
        schema[-4]

    with pytest.raises(IndexError):
        schema[3]


def test_schema_repr_with_dictionaries():
    dct = pa.array(['foo', 'bar', 'baz'], type=pa.string())
    fields = [
        pa.field('one', pa.dictionary(pa.int16(), dct)),
        pa.field('two', pa.int32())
    ]
    sch = pa.schema(fields)

    expected = (
        """\
one: dictionary<values=string, indices=int16, ordered=0>
  dictionary: ["foo", "bar", "baz"]
two: int32""")

    assert repr(sch) == expected


def test_type_schema_pickling():
    cases = [
        pa.int8(),
        pa.string(),
        pa.binary(),
        pa.binary(10),
        pa.list_(pa.string()),
        pa.struct([
            pa.field('a', 'int8'),
            pa.field('b', 'string')
        ]),
        pa.time32('s'),
        pa.time64('us'),
        pa.date32(),
        pa.date64(),
        pa.timestamp('ms'),
        pa.timestamp('ns'),
        pa.decimal(12, 2),
        pa.field('a', 'string', metadata={b'foo': b'bar'})
    ]

    for val in cases:
        roundtripped = pickle.loads(pickle.dumps(val))
        assert val == roundtripped

    fields = []
    for i, f in enumerate(cases):
        if isinstance(f, pa.Field):
            fields.append(f)
        else:
            fields.append(pa.field('_f{}'.format(i), f))

    schema = pa.schema(fields, metadata={b'foo': b'bar'})
    roundtripped = pickle.loads(pickle.dumps(schema))
    assert schema == roundtripped
