"""Serd Python interface"""

import sys

from enum import IntEnum, IntFlag

from ctypes import Structure, CDLL, POINTER, byref
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


class StatementFlags(IntFlag):
    EMPTY_S = 1 << 0  # Empty blank node subject
    ANON_S = 1 << 1  # Start of anonymous subject
    ANON_O = 1 << 2  # Start of anonymous object
    LIST_S = 1 << 3  # Start of list subject
    LIST_O = 1 << 4  # Start of list object
    TERSE_S = 1 << 5  # Terse serialisation of new subject
    TERSE_O = 1 << 6  # Terse serialisation of new object


class SerialisationFlags(IntFlag):
    NO_INLINE_OBJECTS = 1 << 0  # Disable object inlining


class NodeType(IntEnum):
    LITERAL = 1  # Literal value
    URI = 2  # URI (absolute or relative)
    CURIE = 3  # CURIE (shortened URI)
    BLANK = 4  # Blank node
    VARIABLE = 5  # Variable node


class NodeFlags(IntFlag):
    HAS_NEWLINE = 1  # Contains line breaks ('\\n' or '\\r')
    HAS_QUOTE = 1 << 1  # Contains quotes ('"')
    HAS_DATATYPE = 1 << 2  # Literal node has datatype
    HAS_LANGUAGE = 1 << 3  # Literal node has language


class Field(IntEnum):
    SUBJECT = 0  # Subject
    PREDICATE = 1  # Predicate ("key")
    OBJECT = 2  # Object ("value")
    GRAPH = 3  # Graph ("context")


class ModelFlags(IntFlag):
    INDEX_SPO = 1 << 0  # Subject,   Predicate, Object
    INDEX_SOP = 1 << 1  # Subject,   Object,    Predicate
    INDEX_OPS = 1 << 2  # Object,    Predicate, Subject
    INDEX_OSP = 1 << 3  # Object,    Subject,   Predicate
    INDEX_PSO = 1 << 4  # Predicate, Subject,   Object
    INDEX_POS = 1 << 5  # Predicate, Object,    Subject
    INDEX_GRAPHS = 1 << 6  # Support multiple graphs in model
    STORE_CURSORS = 1 << 7  # Store original cursor of statements


# TODO: URI


class ReaderFlags(IntFlag):
    READ_LAX = 1 << 0  # Tolerate invalid input where possible
    READ_VARIABLES = 1 << 1  # Support variable nodes


class WriterFlags(IntFlag):
    WRITE_ASCII = 1 << 0  # Escape all non-ASCII characters
    WRITE_TERSE = 1 << 1  # Write terser output without newlines
    WRITE_LAX = 1 << 2  # Tolerate lossy output


# String Utilities


def strerror(status):
    return c.strerror(status).decode("utf-8")


def strtod(string):
    return c.strtod(string, c_size_t(0))


# Base64

# _cfunc("base64_encoded_length", c_size_t, c_size_t, c_bool)
# _cfunc("base64_decoded_size", c_size_t, c_size_t)
# _cfunc("base64_encode", c_bool, String, c_void_p, c_size_t, c_bool)
# _cfunc("base64_decode", Status, c_void_p, c_size_t, String, c_size_t)


def base64_encode(data, wrap_lines=False):
    size = len(data)
    length = c.base64_encoded_length(size, wrap_lines)
    result = bytes(length)
    status = c.base64_encode(result, data, size, wrap_lines)

    return result.decode("utf-8") if status == Status.SUCCESS else None


def base64_decode(string):
    length = len(string)
    size = c.base64_decoded_size(length)
    result = bytes(size)
    actual_size = c_size_t(0)

    c.base64_decode(result, byref(actual_size), string, length)
    assert actual_size.value <= size

    return result[0 : actual_size.value]


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
    def manage(cls, node):
        assert node is None or type(node) == P(Node)
        return Node(node) if node else None

    @classmethod
    def wrap(cls, node):
        return Node.manage(c.node_copy(node))

    @classmethod
    def string(cls, s):
        return Node.manage(c.new_string(s))

    @classmethod
    def plain_literal(cls, s, lang):
        return Node.manage(c.new_plain_literal(s, lang))

    @classmethod
    def typed_literal(cls, s, datatype):
        return Node.manage(c.new_typed_literal(s, datatype.node))

    @classmethod
    def blank(cls, s):
        return Node.manage(c.new_blank(s))

    @classmethod
    def curie(cls, s):
        return Node.manage(c.new_curie(s))

    @classmethod
    def uri(cls, s):
        return Node.manage(c.new_uri(s))

    @classmethod
    def resolved_uri(cls, s, base):
        return Node.manage(c.new_resolved_uri(s, base.node))

    @classmethod
    def file_uri(cls, path, hostname):
        return Node.manage(c.new_file_uri(path, hostname))

    @classmethod
    def relative_uri(cls, s, base, root):
        return Node.manage(c.new_relative_uri(s, base, root))

    @classmethod
    def decimal(cls, d, max_precision, max_frac_digits, datatype):
        return Node.manage(
            c.new_decimal(d, max_precision, max_frac_digits, datatype)
        )

    @classmethod
    def double(cls, d):
        return Node.manage(c.new_double(d))

    @classmethod
    def float(cls, f):
        return Node.manage(c.new_float(f))

    @classmethod
    def integer(cls, i, datatype=None):
        return Node.manage(c.new_integer(i, datatype.node if datatype else None))

    @classmethod
    def boolean(cls, b):
        return Node.manage(c.new_boolean(b))

    @classmethod
    def blob(cls, buf, wrap_lines=False, datatype=None):
        assert type(wrap_lines) == bool
        assert datatype is None or type(datatype) == Node
        return Node.manage(
            c.new_blob(
                buf, len(buf), wrap_lines, datatype.node if datatype else None
            )
        )

    def __init__(self, arg):
        # TODO: test
        if type(arg) == POINTER(Node):
            self.node = arg
        elif isinstance(arg, str):
            self.node = c.new_string(arg)
        elif isinstance(arg, float):
            self.node = c.new_double(arg)
        else:
            raise TypeError("Bad argument type for Node(): %s" % type(arg))

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

    def __lt__(self, rhs):
        return c.node_compare(self.node, rhs.node) < 0

    def __le__(self, rhs):
        return c.node_compare(self.node, rhs.node) <= 0

    def type(self):
        return NodeType(c.node_get_type(self.node))

    def datatype(self):
        return Node.wrap(c.node_get_datatype(self.node))

    def language(self):
        return Node.wrap(c.node_get_language(self.node))

    def flags(self):
        return c.node_get_flags(self.node)


class Env(Structure):
    @classmethod
    def manage(cls, env):
        assert env is None or type(env) == P(Env)
        return Env(env) if env else None

    def __init__(self, arg=None):
        if arg is None:
            self.env = c.env_new(None)
        elif type(arg) == P(Env):
            self.env = arg
        elif type(arg) == Env:
            self.env = c.env_copy(arg.env)
        elif type(arg) == Node:
            self.env = c.env_new(arg.node)
        else:
            raise TypeError("Bad argument type for Env(): %s" % type(arg))

    def __del(self):
        c.env_free(self.env)
        self.env = None

    def __eq__(self, rhs):
        return type(rhs) == Env and c.env_equals(self.env, rhs.env)

    def base_uri(self):
        return Node.wrap(c.env_get_base_uri(self.env))

    def set_base_uri(self, uri):
        node = uri.node if uri is not None else None
        return Status(c.env_set_base_uri(self.env, node))

    def set_prefix(self, name, uri):
        name_node = Node.string(name) if type(name) == str else name
        return Status(c.env_set_prefix(self.env, name_node.node, uri.node))

    def qualify(self, node):
        return Node.manage(c.env_qualify(self.env, node.node))

    def expand(self, node):
        return Node.manage(c.env_expand(self.env, node.node))


class Statement(Structure):
    @classmethod
    def manage(cls, statement):
        assert statement is None or type(statement) == P(Statement)
        return Statement(ptr=statement) if statement else None

    def __init__(
        self,
        subject=None,
        predicate=None,
        object=None,
        graph=None,
        cursor=None,
        ptr=None,
    ):
        if ptr and type(ptr) == POINTER(Statement):
            self.statement = arg
        elif not (subject and predicate and object):
            raise TypeError("Missing field for Statement()")

        self.statement = c.statement_new(
            subject.node,
            predicate.node,
            object.node,
            graph.node if graph else None,
            cursor.cursor if cursor else None,
        )

    def __del__(self):
        c.statement_free(self.statement)
        self.statement = None

    def __eq__(self, rhs):
        return type(rhs) == Statement and c.statement_equals(
            self.statement, rhs.statement
        )

    def matches(self, s, p, o, g=None):
        return c.statement_matches(
            self.statement,
            s.node if s is not None else None,
            p.node if p is not None else None,
            o.node if o is not None else None,
            g.node if g is not None else None,
        )

    def node(self, field):
        return Node.wrap(c.statement_get_node(self.statement, field))

    def subject(self):
        return Node.wrap(c.statement_get_subject(self.statement))

    def predicate(self):
        return Node.wrap(c.statement_get_predicate(self.statement))

    def object(self):
        return Node.wrap(c.statement_get_object(self.statement))

    def graph(self):
        return Node.wrap(c.statement_get_graph(self.statement))

    def cursor(self):
        return Cursor.wrap(c.statement_get_cursor(self.statement))


class Cursor(Structure):
    @classmethod
    def manage(cls, cursor):
        assert cursor is None or type(cursor) == P(Cursor)
        return Cursor(cursor) if cursor else None

    @classmethod
    def wrap(cls, cursor):
        return Cursor.manage(c.cursor_copy(cursor))

    def __init__(self, arg, line=1, col=0):
        if type(arg) == POINTER(Cursor):
            self.cursor = arg
        elif type(arg) == Node:
            self.cursor = c.cursor_new(arg.node, line, col)
        elif type(arg) == str:
            self.cursor = c.cursor_new(Node.string(arg).node, line, col)
        else:
            raise TypeError("Bad argument type for Cursor(): %s" % type(arg))

    def __del__(self):
        c.cursor_free(self.cursor)
        self.cursor = None

    def __eq__(self, rhs):
        return type(rhs) == Cursor and c.cursor_equals(self.cursor, rhs.cursor)

    def name(self):
        return Node.wrap(c.cursor_get_name(self.cursor))

    def line(self):
        return c.cursor_get_line(self.cursor)

    def column(self):
        return c.cursor_get_column(self.cursor)


# Set up C bindings

class String(str):
    # Wrapper for string parameters to pass as raw C UTF-8 strings
    @classmethod
    def from_param(cls, obj):
        return obj.encode("utf-8")


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
_cfunc("strtod", c_double, String, POINTER(c_size_t))

# Base64
_cfunc("base64_encoded_length", c_size_t, c_size_t, c_bool)
_cfunc("base64_decoded_size", c_size_t, c_size_t)
_cfunc("base64_encode", c_bool, c_char_p, c_void_p, c_size_t, c_bool)
_cfunc("base64_decode", Status, c_void_p, P(c_size_t), String, c_size_t)


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
_cfunc("new_uri", P(Node), String)
_cfunc("new_resolved_uri", P(Node), String, P(Node))
# _cfunc("node_normalise", P(Node), P(Env), P(Node))
_cfunc("node_resolve", P(Node), P(Node))
_cfunc("new_file_uri", P(Node), String, String)
_cfunc("new_relative_uri", P(Node), String, P(Node), P(Node))
_cfunc("new_decimal", P(Node), c_double, c_uint, c_uint, P(Node))
_cfunc("new_double", P(Node), c_double)
_cfunc("new_float", P(Node), c_float)
_cfunc("new_integer", P(Node), c_int64, P(Node))
_cfunc("new_boolean", P(Node), c_bool)
_cfunc("new_blob", P(Node), c_void_p, c_size_t, c_bool, P(Node))
_cfunc("node_copy", P(Node), P(Node))
_cfunc("node_get_type", NodeType, P(Node))
_cfunc("node_get_string", c_char_p, P(Node))
_cfunc("node_get_length", c_size_t, P(Node))
_cfunc("node_get_flags", NodeFlags, P(Node))
_cfunc("node_get_datatype", P(Node), P(Node))
_cfunc("node_get_language", P(Node), P(Node))
_cfunc("node_equals", c_bool, P(Node), P(Node))
_cfunc("node_compare", c_int, P(Node), P(Node))

# Env
_cfunc("env_new", P(Env), P(Node))
_cfunc("env_copy", P(Env), P(Env))
_cfunc("env_equals", c_bool, P(Env), P(Env))
_cfunc("env_free", None, P(Env))
_cfunc("env_get_base_uri", P(Node), P(Env))
_cfunc("env_set_base_uri", Status, P(Env), P(Node))
_cfunc("env_set_prefix", Status, P(Env), P(Node), P(Node))
# _cfunc("env_set_prefix_from_strings", Status, P(Env), c_char_p, c_char_p)
_cfunc("env_qualify", P(Node), P(Env), P(Node))
_cfunc("env_expand", P(Node), P(Env), P(Node))
# _cfunc("env_write_prefixes", None, P(Env), P(Sink))

# Statement

_cfunc(
    "statement_new", P(Statement), P(Node), P(Node), P(Node), P(Node), P(Cursor)
)

_cfunc("statement_copy", P(Statement), P(Statement))
_cfunc("statement_free", None, P(Statement))
_cfunc("statement_get_node", P(Node), P(Statement), c_int)
_cfunc("statement_get_subject", P(Node), P(Statement))
_cfunc("statement_get_predicate", P(Node), P(Statement))
_cfunc("statement_get_object", P(Node), P(Statement))
_cfunc("statement_get_graph", P(Node), P(Statement))
_cfunc("statement_get_cursor", P(Cursor), P(Statement))
_cfunc("statement_equals", c_bool, P(Statement), P(Statement))

_cfunc(
    "statement_matches",
    c_bool,
    P(Statement),
    P(Node),
    P(Node),
    P(Node),
    P(Node),
)

# Cursor
_cfunc("cursor_new", P(Cursor), P(Node), c_uint, c_uint)
_cfunc("cursor_copy", P(Cursor), P(Cursor))
_cfunc("cursor_free", None, P(Cursor))
_cfunc("cursor_equals", c_bool, P(Cursor), P(Cursor))
_cfunc("cursor_get_name", P(Node), P(Cursor))
_cfunc("cursor_get_line", c_uint, P(Cursor))
_cfunc("cursor_get_column", c_uint, P(Cursor))
