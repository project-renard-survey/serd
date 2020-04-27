"""Serd Python interface"""

import sys

from enum import IntEnum

from ctypes import Structure, CDLL, POINTER
from ctypes import c_bool, c_double, c_float, c_int, c_uint
from ctypes import c_size_t, c_int64
from ctypes import c_char_p, c_void_p


class _SerdLib:
    """Object that represents the libserd C library"""

    def __init__(self):
        if sys.platform == "darwin":
            self.lib = CDLL("libserd-1.dylib")
        elif sys.platform == "win32":
            self.lib = CDLL("serd-1.dll")
        else:
            self.lib = CDLL("libserd-1.so")


# Load C library and define library global (which is populated below)
c = _SerdLib()


class Status(IntEnum):
    SUCCESS = 0  # No error
    FAILURE = 1  # Non-fatal failure
    ERR_UNKNOWN = 2  # Unknown error
    ERR_BAD_SYNTAX = 3  # Invalid syntax
    ERR_BAD_ARG = 4  # Invalid argument
    ERR_BAD_ITER = 5  # Use of invalidated iterator
    ERR_NOT_FOUND = 6  # Not found
    ERR_ID_CLASH = 7  # Encountered clashing blank node IDs
    ERR_BAD_CURIE = 8  # Invalid CURIE (e.g. prefix does not exist)
    ERR_INTERNAL = 9  # Unexpected internal error (should not happen)
    ERR_OVERFLOW = 10  # Stack overflow
    ERR_INVALID = 11  # Invalid data
    ERR_NO_DATA = 12  # Unexpected end of input
    ERR_BAD_WRITE = 13  # Error writing to file/stream


class Syntax(IntEnum):
    EMPTY = 0  # Empty syntax (suppress input or output)
    TURTLE = 1  # Terse triples http://www.w3.org/TR/turtle
    NTRIPLES = 2  # Flat triples http://www.w3.org/TR/n-triples/
    NQUADS = 3  # Flat quads http://www.w3.org/TR/n-quads/
    TRIG = 4  # Terse quads http://www.w3.org/TR/trig/


class StatementFlag(IntEnum):
    EMPTY_S = 1 << 0  # Empty blank node subject
    ANON_S = 1 << 1  # Start of anonymous subject
    ANON_O = 1 << 2  # Start of anonymous object
    LIST_S = 1 << 3  # Start of list subject
    LIST_O = 1 << 4  # Start of list object
    TERSE_S = 1 << 5  # Terse serialisation of new subject
    TERSE_O = 1 << 6  # Terse serialisation of new object


class SerialisationFlag(IntEnum):
    NO_INLINE_OBJECTS = 1 << 0  # Disable object inlining


class NodeType(IntEnum):
    LITERAL = 1  # Literal value
    URI = 2  # URI (absolute or relative)
    CURIE = 3  # CURIE (shortened URI)
    BLANK = 4  # Blank node
    VARIABLE = 5  # Variable node


class NodeFlag(IntEnum):
    HAS_NEWLINE = 1  # Contains line breaks ('\\n' or '\\r')
    HAS_QUOTE = 1 << 1  # Contains quotes ('"')
    HAS_DATATYPE = 1 << 2  # Literal node has datatype
    HAS_LANGUAGE = 1 << 3  # Literal node has language


class Field(IntEnum):
    SUBJECT = 0  # Subject
    PREDICATE = 1  # Predicate ("key")
    OBJECT = 2  # Object ("value")
    GRAPH = 3  # Graph ("context")


class ModelFlag(IntEnum):
    INDEX_SPO = 1 << 0  # Subject,   Predicate, Object
    INDEX_SOP = 1 << 1  # Subject,   Object,    Predicate
    INDEX_OPS = 1 << 2  # Object,    Predicate, Subject
    INDEX_OSP = 1 << 3  # Object,    Subject,   Predicate
    INDEX_PSO = 1 << 4  # Predicate, Subject,   Object
    INDEX_POS = 1 << 5  # Predicate, Object,    Subject
    INDEX_GRAPHS = 1 << 6  # Support multiple graphs in model
    STORE_CURSORS = 1 << 7  # Store original cursor of statements


# TODO: URI


class ReaderFlag(IntEnum):
    READ_LAX = 1 << 0  # Tolerate invalid input where possible
    READ_VARIABLES = 1 << 1  # Support variable nodes


class WriterFlag(IntEnum):
    WRITE_ASCII = 1 << 0  # Escape all non-ASCII characters
    WRITE_TERSE = 1 << 1  # Write terser output without newlines
    WRITE_LAX = 1 << 2  # Tolerate lossy output


class World(Structure):
    def __init__(self):
        self.world = c.world_new()

    def __del__(self):
        c.world_free(self.world)
        self.world = None


class Nodes(Structure):
    def __del__(self):
        c.world_free(self.world)
        self.world = None


class Node(Structure):
    @classmethod
    def wrap(cls, node):
        assert type(node) == P(Node)
        return Node(node) if node else None

    @classmethod
    def string(cls, s):
        return Node.wrap(c.new_string(s))

    @classmethod
    def plain_literal(cls, s, lang):
        return Node.wrap(c.new_plain_literal(s, lang))

    @classmethod
    def typed_literal(cls, s, datatype):
        return Node.wrap(c.new_typed_literal(s, datatype.node))

    @classmethod
    def blank(cls, s):
        return Node.wrap(c.new_blank(s))

    @classmethod
    def curie(cls, s):
        return Node.wrap(c.new_curie(s))

    @classmethod
    def uri(cls, s):
        return Node.wrap(c.new_uri(s))

    @classmethod
    def resolved_uri(cls, s, base):
        return Node.wrap(c.new_resolved_uri(s, base.node))

    @classmethod
    def file_uri(cls, path, hostname):
        return Node.wrap(c.new_file_uri(path, hostname))

    @classmethod
    def relative_uri(cls, s, base, root):
        return Node.wrap(c.new_relative_uri(s, base, root))

    @classmethod
    def decimal(cls, d, max_precision, max_frac_digits, datatype):
        return Node.wrap(
            c.new_decimal(d, max_precision, max_frac_digits, datatype)
        )

    @classmethod
    def double(cls, d):
        return Node.wrap(c.new_double(d))

    @classmethod
    def float(cls, f):
        return Node.wrap(c.new_float(f))

    @classmethod
    def integer(cls, i, datatype=None):
        return Node.wrap(c.new_integer(i, datatype.node if datatype else None))

    @classmethod
    def boolean(cls, b):
        return Node.wrap(c.new_boolean(b))

    @classmethod
    def blob(cls, buf, wrap_lines=False, datatype=None):
        assert type(wrap_lines) == bool
        assert datatype is None or type(datatype) == Node
        return Node.wrap(
            c.new_blob(
                buf, len(buf), wrap_lines, datatype.node if datatype else None
            )
        )

    def __init__(self, node):
        assert type(node) == POINTER(Node)
        self.node = node

    def __del(self):
        c.node_free(self.node)
        self.node = None

    def __str__(self):
        return c.node_get_string(self.node).decode("utf-8")

    def __len__(self):
        return c.node_get_length(self.node)

    def __eq__(self, rhs):
        if rhs is None:
            return False

        rhs_type = type(rhs)
        if rhs_type == Node:
            return c.node_equals(self.node, rhs.node)

        return rhs_type(self) == rhs

    def type(self):
        return NodeType(c.node_get_type(self.node))

    def datatype(self):
        return Node.wrap(c.node_copy(c.node_get_datatype(self.node)))

    def language(self):
        return Node.wrap(c.node_copy(c.node_get_language(self.node)))

    def flags(self):
        return c.node_get_flags(self.node)


# Set up C bindings
def _is_string(obj):
    if sys.version_info[0] == 3:
        return isinstance(obj, str)
    else:
        return isinstance(obj, basestring)


class String(str):
    # Wrapper for string parameters to pass as raw C UTF-8 strings
    def from_param(cls, obj):
        assert _is_string(obj)
        return obj.encode("utf-8")

    from_param = classmethod(from_param)


def _cfunc(name, restype, *argtypes):
    """Set the `name` attribute of the `c` global to a C function"""
    assert isinstance(c, _SerdLib)
    f = getattr(c.lib, "serd_" + name)
    f.restype = restype
    f.argtypes = argtypes
    setattr(c, name, f)


def P(x):
    """Shorthand for ctypes.POINTER"""
    return POINTER(x)


_cfunc("free", None, c_void_p)

# String utilities

_cfunc("strerror", c_char_p, c_int)

# _cfunc("strlen", c_size_t, c_char_p, Pointer(NodeFlags))

_cfunc("strtod", c_double, POINTER(c_size_t))


# World
# _cfunc("file_uri_parse", c_char_p, String, P(c_char_p))
_cfunc("world_new", P(World))
_cfunc("world_free", None, P(World))
_cfunc("world_get_nodes", P(Nodes), P(World))
_cfunc("world_get_blank", P(World))

# Node

_cfunc("new_string", P(Node), String)
# new_substring
# new_literal
_cfunc("new_plain_literal", P(Node), String, String)
_cfunc("new_typed_literal", P(Node), String, P(Node))
_cfunc("new_blank", P(Node), String)
_cfunc("new_curie", P(Node), String)

# TODO: Fix order in serd.h
_cfunc("node_copy", P(Node), P(Node))
_cfunc("node_equals", c_bool, P(Node), P(Node))
_cfunc("node_compare", c_int, P(Node), P(Node))

_cfunc("new_uri", P(Node), String)
_cfunc("new_resolved_uri", P(Node), String, P(Node))
# _cfunc("node_normalise", P(Node), P(Env), P(Node))

# TODO: Fix order in serd.h
_cfunc("node_resolve", P(Node), P(Node))

_cfunc("new_file_uri", P(Node), String, String)
_cfunc("new_relative_uri", P(Node), String, P(Node), P(Node))
_cfunc("new_decimal", P(Node), c_double, c_uint, c_uint, P(Node))
_cfunc("new_double", P(Node), c_double)
_cfunc("new_float", P(Node), c_float)
_cfunc("new_integer", P(Node), c_int64, P(Node))
_cfunc("new_boolean", P(Node), c_bool)
_cfunc("new_blob", P(Node), c_void_p, c_size_t, c_bool, P(Node))

NodeFlags = c_int

_cfunc("node_get_type", NodeType, P(Node))
_cfunc("node_get_string", c_char_p, P(Node))
_cfunc("node_get_length", c_size_t, P(Node))
_cfunc("node_get_datatype", P(Node), P(Node))
_cfunc("node_get_language", P(Node), P(Node))
_cfunc("node_get_flags", NodeFlags, P(Node))
