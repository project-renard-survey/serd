# Copyright 2020 David Robillard <d@drobilla.net>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import serd
import unittest
import base64
import math


class StringTests(unittest.TestCase):
    def testStrerror(self):
        self.assertEqual(serd.strerror(serd.Status.SUCCESS), "Success")
        self.assertEqual(
            serd.strerror(serd.Status.ERR_BAD_WRITE), "Error writing to file"
        )

    def testStrtod(self):
        self.assertEqual(serd.strtod("42"), 42.0)
        self.assertEqual(serd.strtod("1.234 hello"), 1.234)
        self.assertTrue(math.isnan(serd.strtod("not a number")))


class Base64Tests(unittest.TestCase):
    def testBase64(self):
        data = "foobar".encode("utf-8")
        encoded = "Zm9vYmFy"

        self.assertEqual(serd.base64_encode(data), encoded)
        self.assertEqual(serd.base64_decode(encoded), data)


class NodeTests(unittest.TestCase):
    def testString(self):
        n = serd.Node.string("hello")
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "hello")
        self.assertEqual(len(n), 5)
        self.assertIsNone(n.datatype())
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), 0)

    def testPlainLiteral(self):
        n = serd.Node.plain_literal("hallo", "de")
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "hallo")
        self.assertEqual(len(n), 5)
        self.assertIsNone(n.datatype())
        self.assertEqual(n.language(), serd.Node.string("de"))
        self.assertEqual(n.flags(), serd.NodeFlags.HAS_LANGUAGE)

    def testTypedLiteral(self):
        datatype = serd.Node.uri("http://example.org/ns#Hex")
        n = serd.Node.typed_literal("ABCD", datatype)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "ABCD")
        self.assertEqual(len(n), 4)
        self.assertEqual(n.datatype(), datatype)
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlags.HAS_DATATYPE)

    def testBlank(self):
        n = serd.Node.blank("b0")
        self.assertEqual(n.type(), serd.NodeType.BLANK)
        self.assertEqual(n, "b0")
        self.assertEqual(len(n), 2)
        self.assertIsNone(n.datatype())
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), 0)

    def testCurie(self):
        n = serd.Node.curie("ns:name")
        self.assertEqual(n.type(), serd.NodeType.CURIE)
        self.assertEqual(n, "ns:name")
        self.assertEqual(len(n), 7)
        self.assertIsNone(n.datatype())
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), 0)

    def testUri(self):
        n = serd.Node.uri("http://example.org/")
        self.assertEqual(n.type(), serd.NodeType.URI)
        self.assertEqual(n, "http://example.org/")
        self.assertEqual(len(n), 19)
        self.assertIsNone(n.datatype())
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), 0)

    def testResolvedUri(self):
        base = serd.Node.uri("http://example.org/")
        n = serd.Node.resolved_uri("name", base)
        self.assertEqual(n.type(), serd.NodeType.URI)
        self.assertEqual(n, "http://example.org/name")
        self.assertEqual(len(n), 23)
        self.assertIsNone(n.datatype())
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), 0)

    def testFileUri(self):
        base = serd.Node.uri("http://example.org/")
        n = serd.Node.file_uri("/foo/bar", "host")
        self.assertEqual(n.type(), serd.NodeType.URI)
        self.assertEqual(n, "file://host/foo/bar")
        self.assertEqual(len(n), 19)
        self.assertIsNone(n.datatype())
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), 0)

    def testRelativeUri(self):
        base = serd.Node.uri("http://example.org/")
        n = serd.Node.file_uri("/foo/bar", "host")
        self.assertEqual(n.type(), serd.NodeType.URI)
        self.assertEqual(n, "file://host/foo/bar")
        self.assertEqual(len(n), 19)
        self.assertIsNone(n.datatype())
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), 0)

    def testDecimal(self):
        xsd_decimal = "http://www.w3.org/2001/XMLSchema#decimal"
        n = serd.Node.decimal(12.34, 7, 4, None)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(str(n), "12.34")
        self.assertEqual(len(n), 5)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_decimal))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlags.HAS_DATATYPE)

    def testDouble(self):
        xsd_double = "http://www.w3.org/2001/XMLSchema#double"
        n = serd.Node.double(12.34)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "1.234E1")
        self.assertEqual(len(n), 7)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_double))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlags.HAS_DATATYPE)

    def testFloat(self):
        xsd_float = "http://www.w3.org/2001/XMLSchema#float"
        n = serd.Node.float(234.5)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "2.345E2")
        self.assertEqual(len(n), 7)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_float))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlags.HAS_DATATYPE)

    def testInteger(self):
        xsd_integer = "http://www.w3.org/2001/XMLSchema#integer"
        n = serd.Node.integer(42)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "42")
        self.assertEqual(len(n), 2)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_integer))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlags.HAS_DATATYPE)

        xsd_decimal = "http://www.w3.org/2001/XMLSchema#decimal"
        d = serd.Node.integer(53, serd.Node.uri(xsd_decimal))
        self.assertEqual(d.datatype(), serd.Node.uri(xsd_decimal))

    def testBoolean(self):
        xsd_boolean = "http://www.w3.org/2001/XMLSchema#boolean"
        t = serd.Node.boolean(True)
        self.assertEqual(t.type(), serd.NodeType.LITERAL)
        self.assertEqual(str(t), "true")
        self.assertEqual(len(t), 4)
        self.assertEqual(t.datatype(), serd.Node.uri(xsd_boolean))
        self.assertIsNone(t.language())
        self.assertEqual(t.flags(), serd.NodeFlags.HAS_DATATYPE)

        f = serd.Node.boolean(False)
        self.assertEqual(f.type(), serd.NodeType.LITERAL)
        self.assertEqual(str(f), "false")
        self.assertEqual(len(f), 5)
        self.assertEqual(f.datatype(), serd.Node.uri(xsd_boolean))
        self.assertIsNone(f.language())
        self.assertEqual(f.flags(), serd.NodeFlags.HAS_DATATYPE)

    def testBlob(self):
        xsd_base64Binary = "http://www.w3.org/2001/XMLSchema#base64Binary"
        n = serd.Node.blob(b"DEAD")
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(bytes(str(n), "utf-8"), base64.b64encode(b"DEAD"))
        self.assertEqual(len(n), 8)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_base64Binary))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlags.HAS_DATATYPE)

        datatype = "http://example.org/ns#Blob"
        t = serd.Node.blob(b"BEEF", datatype=serd.Node.uri(datatype))
        self.assertEqual(t.type(), serd.NodeType.LITERAL)
        self.assertEqual(bytes(str(t), "utf-8"), base64.b64encode(b"BEEF"))
        self.assertEqual(len(t), 8)
        self.assertEqual(t.datatype(), serd.Node.uri(datatype))
        self.assertIsNone(t.language())
        self.assertEqual(t.flags(), serd.NodeFlags.HAS_DATATYPE)

    def testComparison(self):
        a = serd.Node.string("Aardvark")
        b = serd.Node.string("Banana")

        self.assertEqual(a, a)
        self.assertNotEqual(a, b)
        self.assertLess(a, b)
        self.assertLessEqual(a, b)
        self.assertLessEqual(a, a)
        self.assertGreater(b, a)
        self.assertGreaterEqual(b, a)
        self.assertGreaterEqual(b, b)


class Env(unittest.TestCase):
    def testEquality(self):
        uri = serd.Node.uri("http://example.org/")
        env1 = serd.Env()
        env2 = serd.Env()
        self.assertEqual(env1, env2)

        env2.set_base_uri(uri)
        self.assertNotEqual(env1, env2)

        env2.set_base_uri(None)
        self.assertEqual(env1, env2)

        env2.set_prefix("eg", uri)
        self.assertNotEqual(env1, env2)

        env1.set_prefix(serd.Node.string("eg"), uri)
        self.assertEqual(env1, env2)

    def testBaseUri(self):
        env = serd.Env()
        self.assertIsNone(env.base_uri())

        base = serd.Node.uri("http://example.org/")
        env.set_base_uri(base)
        self.assertEqual(env.base_uri(), base)

    def testInitialBaseUri(self):
        base = serd.Node.uri("http://example.org/")
        env = serd.Env(base)
        self.assertEqual(env.base_uri(), base)

    def testQualify(self):
        base = serd.Node.uri("http://example.org/")
        uri = serd.Node.uri("http://example.org/name")
        env = serd.Env(base)

        self.assertIsNone(env.qualify(uri))

        env.set_prefix("eg", base)
        self.assertEqual(env.qualify(uri), "eg:name")

    def testExpand(self):
        base = serd.Node.uri("http://example.org/")
        curie = serd.Node.curie("eg:name")
        env = serd.Env(base)

        self.assertIsNone(env.expand(curie))

        env.set_prefix("eg", base)
        self.assertEqual(
            env.expand(curie), serd.Node.uri("http://example.org/name")
        )


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.world = serd.World()
        self.s = serd.Node.uri("http://example.org/s")
        self.p = serd.Node.uri("http://example.org/p")
        self.o = serd.Node.uri("http://example.org/o")
        self.g = serd.Node.uri("http://example.org/g")

    def testConstruction(self):
        flags = serd.ModelFlags.INDEX_SPO | serd.ModelFlags.INDEX_GRAPHS
        model = serd.Model(self.world, flags)
        self.assertEqual(model.flags(), flags)
        self.assertNotEqual(model.flags(), serd.ModelFlags.INDEX_SPO)
        self.assertEqual(model.world(), self.world)

    def testInsertErase(self):
        model = serd.Model(self.world, serd.ModelFlags.INDEX_SPO)

        model.insert(self.s, self.p, self.o)
        self.assertEqual(len(model), 1)
        model.erase(iter(model))
        self.assertEqual(len(model), 0)

        statement = serd.Statement(self.s, self.p, self.o)
        model += statement
        self.assertEqual(len(model), 1)
        del model[statement]
        self.assertEqual(len(model), 0)

    def testSize(self):
        model = serd.Model(self.world, serd.ModelFlags.INDEX_SPO)
        self.assertEqual(model.size(), 0)
        self.assertEqual(len(model), 0)
        self.assertTrue(model.empty())

        model.insert(self.s, self.p, self.o)
        self.assertEqual(model.size(), 1)
        self.assertEqual(len(model), 1)
        self.assertFalse(model.empty())

        model.erase(iter(model))
        self.assertEqual(model.size(), 0)
        self.assertEqual(len(model), 0)
        self.assertTrue(model.empty())

    def testBeginEnd(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        model = serd.Model(self.world, serd.ModelFlags.INDEX_SPO)

        self.assertEqual(model.begin(), model.end())

        model.insert(s, p, o, g)
        self.assertNotEqual(model.begin(), model.end())

    def testFind(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        x = serd.Node.uri("http://example.org/x")
        flags = serd.ModelFlags.INDEX_SPO | serd.ModelFlags.INDEX_GRAPHS
        model = serd.Model(self.world, flags)
        in_statement = serd.Statement(s, p, o, g)
        out_statement = serd.Statement(x, p, o, g)

        model += in_statement
        self.assertEqual(model.find(out_statement), model.end())
        self.assertNotEqual(model.find(in_statement), model.end())

    def testGet(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        x = serd.Node.uri("http://example.org/x")
        flags = serd.ModelFlags.INDEX_SPO | serd.ModelFlags.INDEX_GRAPHS
        model = serd.Model(self.world, flags)

        model.insert(s, p, o, g)
        self.assertEqual(model.get(None, p, o, g), s)
        self.assertEqual(model.get(s, None, o, g), p)
        self.assertEqual(model.get(s, p, None, g), o)
        self.assertEqual(model.get(s, p, o, None), g)

    def testAsk(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        x = serd.Node.uri("http://example.org/x")
        flags = serd.ModelFlags.INDEX_SPO | serd.ModelFlags.INDEX_GRAPHS
        model = serd.Model(self.world, flags)
        model.insert(s, p, o, g)

        self.assertTrue(model.ask(s, p, o, g))
        self.assertIn(serd.Statement(s, p, o, g), model)
        self.assertIn((s, p, o, g), model)

        self.assertFalse(model.ask(x, p, o, g))
        self.assertNotIn(serd.Statement(x, p, o, g), model)
        self.assertNotIn((x, p, o, g), model)


class StatementTests(unittest.TestCase):
    def setUp(self):
        self.s = serd.Node.uri("http://example.org/s")
        self.p = serd.Node.uri("http://example.org/p")
        self.o = serd.Node.uri("http://example.org/o")
        self.g = serd.Node.uri("http://example.org/g")
        self.cursor = serd.Cursor("foo.ttl", 1, 0)

    def testAllFields(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        statement = serd.Statement(s, p, o, g, self.cursor)

        self.assertEqual(statement.node(serd.Field.SUBJECT), s)
        self.assertEqual(statement.node(serd.Field.PREDICATE), p)
        self.assertEqual(statement.node(serd.Field.OBJECT), o)
        self.assertEqual(statement.node(serd.Field.GRAPH), g)

        self.assertEqual(statement.subject(), s)
        self.assertEqual(statement.predicate(), p)
        self.assertEqual(statement.object(), o)
        self.assertEqual(statement.graph(), g)

        self.assertEqual(statement.cursor(), self.cursor)

    def testNoGraph(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        statement = serd.Statement(s, p, o, None, self.cursor)

        self.assertEqual(statement.node(serd.Field.SUBJECT), s)
        self.assertEqual(statement.node(serd.Field.PREDICATE), p)
        self.assertEqual(statement.node(serd.Field.OBJECT), o)
        self.assertIsNone(statement.node(serd.Field.GRAPH))

        self.assertEqual(statement.subject(), s)
        self.assertEqual(statement.predicate(), p)
        self.assertEqual(statement.object(), o)
        self.assertIsNone(statement.graph())

        self.assertEqual(statement.cursor(), self.cursor)

    def testNoCursor(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        statement = serd.Statement(s, p, o, g)

        self.assertEqual(statement.node(serd.Field.SUBJECT), s)
        self.assertEqual(statement.node(serd.Field.PREDICATE), p)
        self.assertEqual(statement.node(serd.Field.OBJECT), o)
        self.assertEqual(statement.node(serd.Field.GRAPH), g)

        self.assertEqual(statement.subject(), s)
        self.assertEqual(statement.predicate(), p)
        self.assertEqual(statement.object(), o)
        self.assertEqual(statement.graph(), g)

        self.assertIsNone(statement.cursor())

    def testNoGraphOrCursor(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        statement = serd.Statement(s, p, o)

        self.assertEqual(statement.node(serd.Field.SUBJECT), s)
        self.assertEqual(statement.node(serd.Field.PREDICATE), p)
        self.assertEqual(statement.node(serd.Field.OBJECT), o)
        self.assertIsNone(statement.node(serd.Field.GRAPH))

        self.assertEqual(statement.subject(), s)
        self.assertEqual(statement.predicate(), p)
        self.assertEqual(statement.object(), o)
        self.assertIsNone(statement.graph())

        self.assertIsNone(statement.cursor())

    def testComparison(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        statement1 = serd.Statement(s, p, o, g)
        statement2 = serd.Statement(o, p, s, g)

        self.assertEqual(statement1, statement1)
        self.assertNotEqual(statement1, statement2)

    def testMatches(self):
        s, p, o, g = self.s, self.p, self.o, self.g
        x = serd.Node.uri("http://example.org/x")
        statement = serd.Statement(s, p, o, g)

        self.assertTrue(statement.matches(s, p, o, g))
        self.assertTrue(statement.matches(None, p, o, g))
        self.assertTrue(statement.matches(s, None, o, g))
        self.assertTrue(statement.matches(s, p, None, g))
        self.assertTrue(statement.matches(s, p, o, None))

        self.assertFalse(statement.matches(x, p, o, g))
        self.assertFalse(statement.matches(s, x, o, g))
        self.assertFalse(statement.matches(s, p, x, g))
        self.assertFalse(statement.matches(s, p, o, x))


class RangeTests(unittest.TestCase):
    def setUp(self):
        self.world = serd.World()
        self.s = serd.Node.uri("http://example.org/s")
        self.p = serd.Node.uri("http://example.org/p")
        self.o1 = serd.Node.uri("http://example.org/o1")
        self.o2 = serd.Node.uri("http://example.org/o2")
        self.g = serd.Node.uri("http://example.org/g")

    def testFront(self):
        model = serd.Model(self.world, serd.ModelFlags.INDEX_SPO)

        model.insert(self.s, self.p, self.o1)
        self.assertEqual(model.all().front(), serd.Statement(self.s, self.p, self.o1))

    def testEmpty(self):
        model = serd.Model(self.world, serd.ModelFlags.INDEX_SPO)

        self.assertTrue(model.all().empty())

        model.insert(self.s, self.p, self.o1)
        self.assertFalse(model.all().empty())

    def testIteration(self):
        model = serd.Model(self.world, serd.ModelFlags.INDEX_SPO)

        model.insert(self.s, self.p, self.o1)
        model.insert(self.s, self.p, self.o2)

        i = iter(model.all())
        self.assertEqual(next(i), serd.Statement(self.s, self.p, self.o1))
        self.assertEqual(next(i), serd.Statement(self.s, self.p, self.o2))

        with self.assertRaises(StopIteration):
            next(i)


class CursorTests(unittest.TestCase):
    def testStringConstruction(self):
        cur = serd.Cursor("foo.ttl", 3, 4)
        self.assertEqual(cur.name(), "foo.ttl")
        self.assertEqual(cur.line(), 3)
        self.assertEqual(cur.column(), 4)

    def testNodeConstruction(self):
        name = serd.Node.string("foo.ttl")
        cur = serd.Cursor(name, 5, 6)
        self.assertEqual(cur.name(), name)
        self.assertEqual(cur.line(), 5)
        self.assertEqual(cur.column(), 6)

    def testComparison(self):
        self.assertEqual(
            serd.Cursor("foo.ttl", 1, 2), serd.Cursor("foo.ttl", 1, 2)
        )
        self.assertNotEqual(
            serd.Cursor("foo.ttl", 9, 2), serd.Cursor("foo.ttl", 1, 2)
        )
        self.assertNotEqual(
            serd.Cursor("foo.ttl", 1, 9), serd.Cursor("foo.ttl", 1, 2)
        )
        self.assertNotEqual(
            serd.Cursor("bar.ttl", 1, 2), serd.Cursor("foo.ttl", 1, 2)
        )
