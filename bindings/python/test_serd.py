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
        data = "foobar".encode('utf-8')
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

        self.assertLess(None, a)
        self.assertLessEqual(None, a)
        self.assertGreater(a, None)
        self.assertGreaterEqual(a, None)

    # def get_base_uri(self):
    #     return Node.wrap(c.node_copy(c.env_get_base_uri(self.env)))

    # def set_base_uri(self, uri):
    #     return Status(c.env_set_base_uri(self.env, uri.node))

    # def set_prefix(self, name, uri):
    #     return Status(c.env_set_prefix(self.env, name.node, uri.node))

    # def qualify(self, node):
    #     return Node.wrap(c.env_qualify(self.env, node.node))

    # def expand(self, node):
    #     return Node.wrap(c.env_expand(self.env, node.node))


class Env(unittest.TestCase):
    def setUp(self):
        self.world = serd.World()

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
