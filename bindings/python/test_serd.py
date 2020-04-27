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


class NodeTests(unittest.TestCase):
    def setUp(self):
        self.world = serd.World()

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
        self.assertEqual(n.flags(), serd.NodeFlag.HAS_LANGUAGE)

    def testTypedLiteral(self):
        datatype = serd.Node.uri("http://example.org/ns#Hex")
        n = serd.Node.typed_literal("ABCD", datatype)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "ABCD")
        self.assertEqual(len(n), 4)
        self.assertEqual(n.datatype(), datatype)
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlag.HAS_DATATYPE)

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

    def testDouble(self):
        xsd_double = "http://www.w3.org/2001/XMLSchema#double"
        n = serd.Node.double(12.34)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "1.234E1")
        self.assertEqual(len(n), 7)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_double))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlag.HAS_DATATYPE)

    def testFloat(self):
        xsd_float = "http://www.w3.org/2001/XMLSchema#float"
        n = serd.Node.float(234.5)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "2.345E2")
        self.assertEqual(len(n), 7)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_float))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlag.HAS_DATATYPE)

    def testInteger(self):
        xsd_integer = "http://www.w3.org/2001/XMLSchema#integer"
        n = serd.Node.integer(42)
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(n, "42")
        self.assertEqual(len(n), 2)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_integer))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlag.HAS_DATATYPE)

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
        self.assertEqual(t.flags(), serd.NodeFlag.HAS_DATATYPE)

        f = serd.Node.boolean(False)
        self.assertEqual(f.type(), serd.NodeType.LITERAL)
        self.assertEqual(str(f), "false")
        self.assertEqual(len(f), 5)
        self.assertEqual(f.datatype(), serd.Node.uri(xsd_boolean))
        self.assertIsNone(f.language())
        self.assertEqual(f.flags(), serd.NodeFlag.HAS_DATATYPE)

    def testBlob(self):
        xsd_base64Binary = "http://www.w3.org/2001/XMLSchema#base64Binary"
        n = serd.Node.blob(b"DEAD")
        self.assertEqual(n.type(), serd.NodeType.LITERAL)
        self.assertEqual(bytes(str(n), "utf-8"), base64.b64encode(b"DEAD"))
        self.assertEqual(len(n), 8)
        self.assertEqual(n.datatype(), serd.Node.uri(xsd_base64Binary))
        self.assertIsNone(n.language())
        self.assertEqual(n.flags(), serd.NodeFlag.HAS_DATATYPE)

        datatype = "http://example.org/ns#Blob"
        t = serd.Node.blob(b"BEEF", datatype=serd.Node.uri(datatype))
        self.assertEqual(t.type(), serd.NodeType.LITERAL)
        self.assertEqual(bytes(str(t), "utf-8"), base64.b64encode(b"BEEF"))
        self.assertEqual(len(t), 8)
        self.assertEqual(t.datatype(), serd.Node.uri(datatype))
        self.assertIsNone(t.language())
        self.assertEqual(t.flags(), serd.NodeFlag.HAS_DATATYPE)
