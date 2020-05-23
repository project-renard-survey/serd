"""Serd Python interface"""

import sys

from enum import IntEnum, IntFlag

import ctypes

from ctypes import Structure, CDLL, CFUNCTYPE, POINTER, byref, cast, py_object
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


def strlen(string):
    flags = c_uint(0)
    length = c.strlen(string, byref(flags))
    return (length, NodeFlags(flags.value))


def strtod(string):
    return c.strtod(string, c_size_t(0))


# Base64


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


# Syntax Utilities


def syntax_by_name(name):
    return Syntax(c.syntax_by_name(name))


def guess_syntax(filename):
    return Syntax(c.guess_syntax(filename))


def syntax_has_graphs(syntax):
    return c.syntax_has_graphs(syntax)


# World


class World(Structure):
    def __init__(self):
        self.cobj = c.world_new()

    def __del__(self):
        c.world_free(self.cobj)
        self.cobj = None

    def get_blank(self):
        return Node.wrap(c.world_get_blank(self.cobj))


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
        assert node is None or type(node) == P(Node)
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
        return Node.manage(
            c.new_integer(i, datatype.node if datatype else None)
        )

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

    def __del__(self):
        c.node_free(self.node)
        self.node = None

    def __str__(self):
        return c.node_get_string(self.node).decode("utf-8")

    def __repr__(self):
        # FIXME
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
    def manage(cls, cobj):
        assert cobj is None or type(cobj) == P(Env)
        return Env(cobj) if cobj else None

    def __init__(self, arg=None):
        if arg is None:
            self.cobj = c.env_new(None)
        elif type(arg) == P(Env):
            self.cobj = arg
        elif type(arg) == Env:
            self.cobj = c.env_copy(arg.cobj)
        elif type(arg) == Node:
            self.cobj = c.env_new(arg.node)
        else:
            raise TypeError("Bad argument type for Env(): %s" % type(arg))

    def __del__(self):
        c.env_free(self.cobj)
        self.cobj = None

    def __eq__(self, rhs):
        return type(rhs) == Env and c.env_equals(self.cobj, rhs.cobj)

    def base_uri(self):
        return Node.wrap(c.env_get_base_uri(self.cobj))

    def set_base_uri(self, uri):
        node = uri.node if uri is not None else None
        return Status(c.env_set_base_uri(self.cobj, node))

    def set_prefix(self, name, uri):
        name_node = Node.string(name) if type(name) == str else name
        return Status(c.env_set_prefix(self.cobj, name_node.node, uri.node))

    def qualify(self, node):
        return Node.manage(c.env_qualify(self.cobj, node.node))

    def expand(self, node):
        return Node.manage(c.env_expand(self.cobj, node.node))


class Reader(Structure):
    @classmethod
    def manage(cls, cobj):
        assert cobj is None or type(cobj) == P(Reader)
        return Reader(None, None, None, None, None, cobj=cobj) if cobj else None

    def __init__(self, world, syntax, flags, sink, stack_size, cobj=None):
        if type(cobj) == P(Reader):
            self.cobj = cobj
        else:
            assert type(world) == World
            assert type(syntax) == Syntax
            assert type(flags) == ReaderFlags or type(flags) == int
            assert isinstance(sink, Sink)
            assert type(stack_size) in [int, c_size_t]

            self.cobj = c.reader_new(
                world.cobj, syntax, flags, sink.cobj, stack_size
            )

    def __del__(self):
        c.reader_free(self.cobj)
        self.cobj = None

    def add_blank_prefix(self, prefix):
        c.reader_add_blank_prefix(self.cobj, prefix)

    def start_file(self, uri, bulk=True):
        return c.reader_start_file(self.cobj, uri, bulk)

    def start_string(self, utf8, name):
        return c.reader_start_string(self.cobj, utf8, name)

    def read_chunk(self):
        return c.reader_read_chunk(self.cobj)

    def read_document(self):
        return c.reader_read_document(self.cobj)

    def finish(self):
        return c.reader_finish(self.cobj)


class Model(Structure):
    @classmethod
    def manage(cls, cobj):
        assert cobj is None or type(cobj) == P(Model)
        return Model(cobj=cobj) if cobj else None

    def __init__(self, world, flags=None, model=None, cobj=None):
        assert type(world) == World

        self._world = world

        if type(cobj) == POINTER(Model):
            assert c.model_get_world(cobj) == world.cobj
            self.cobj = cobj
        elif type(model) == Model:
            assert c.model_get_world(model).world == world.cobj
            self.cobj = c.model_copy(arg.model)
        elif flags is not None:
            self.cobj = c.model_new(world.cobj, flags)
        else:
            raise TypeError("Bad arguments for Model()")

        assert self.cobj

    def __del__(self):
        c.model_free(self.cobj)
        self.model = None

    def __eq__(self, rhs):
        return c.model_equals(self.cobj, rhs.cobj)

    def __len__(self):
        return self.size()

    def __iter__(self):
        return Iter.manage(c.model_begin(self.cobj))

    def __contains__(self, statement):
        return self.find(statement) != self.end()

    def __delitem__(self, statement):
        i = self.find(statement)
        if i is not None:
            return self.erase(i)

    def __add__(self, statement):
        status = c.model_insert(self.cobj, Statement.from_param(statement).cobj)
        if status != Status.SUCCESS:
            raise RuntimeError("Failed to insert statement")

        return self

    def world(self):
        return self._world

    def flags(self):
        return ModelFlags(c.model_get_flags(self.cobj))

    def size(self):
        return c.model_size(self.cobj)

    def empty(self):
        return c.model_empty(self.cobj)

    def insert(self, arg):
        if type(arg) == Range:
            return Status(c.model_add_range(self.cobj, arg.cobj))

        statement = Statement.from_param(arg)
        return Status(c.model_insert(self.cobj, statement.cobj))

    def erase(self, arg):
        if type(arg) == Range:
            return Status(c.model_erase_range(self.cobj, arg.cobj))

        return Status(c.model_erase(self.cobj, arg.cobj))

    def begin(self):
        return Iter.manage(c.model_begin(self.cobj))

    def end(self):
        return Iter.wrap(c.model_end(self.cobj))

    def all(self):
        return Range.wrap(c.model_all(self.cobj))

    def find(self, statement):
        statement = Statement.from_param(statement)
        s = statement.subject()
        p = statement.predicate()
        o = statement.object()
        g = statement.graph()

        c_iter = c.model_find(
            self.cobj,
            s.node if s is not None else None,
            p.node if p is not None else None,
            o.node if o is not None else None,
            g.node if g is not None else None,
        )

        return Iter.manage(c_iter) if c_iter else self.end()

    def range(self, pattern):
        assert type(pattern) == tuple
        assert len(pattern) == 3 or len(pattern) == 4

        s = pattern[0]
        p = pattern[1]
        o = pattern[2]
        g = pattern[3] if len(pattern) == 4 else None

        return Range.manage(
            c.model_range(
                self.cobj,
                s.node if s is not None else None,
                p.node if p is not None else None,
                o.node if o is not None else None,
                g.node if g is not None else None,
            )
        )

    def get(self, subject=None, predicate=None, object=None, graph=None):
        return Node.wrap(
            c.model_get(
                self.cobj,
                subject.node if subject is not None else None,
                predicate.node if predicate is not None else None,
                object.node if object is not None else None,
                graph.node if graph is not None else None,
            )
        )

    def ask(self, s, p, o, g=None):
        return c.model_ask(
            self.cobj,
            s.node if s is not None else None,
            p.node if p is not None else None,
            o.node if o is not None else None,
            g.node if g is not None else None,
        )

    def count(self, s, p, o, g=None):
        return c.model_count(
            self.cobj,
            s.node if s is not None else None,
            p.node if p is not None else None,
            o.node if o is not None else None,
            g.node if g is not None else None,
        )


class Inserter(Structure):
    @classmethod
    def manage(cls, cobj):
        assert cobj is None or type(cobj) == P(Model)
        return Inserter(cobj=cobj) if cobj else None

    def __init__(self, model=None, env=None, default_graph=None, cobj=None):
        assert type(world) == World

        self._world = world

        if type(cobj) == POINTER(Inserter):
            self.cobj = cobj
        elif (
            type(model) == Model
            and type(env) == Env
            and type(default_graph) == Node
        ):
            self.cobj = c.inserter_new(model.cobj, env.cobj, default_graph.cobj)
        else:
            raise TypeError("Bad arguments for Inserter()")

        assert self.cobj

    def __del__(self):
        c.inserter_free(self.cobj)
        self.cobj = None

    def sink(self):
        return Sink(c.inserter_get_sink(self.cobj))


class Statement(Structure):
    @classmethod
    def manage(cls, statement):
        assert statement is None or type(statement) == P(Statement)
        return Statement(ptr=statement) if statement else None

    @classmethod
    def wrap(cls, cobj):
        return Statement.manage(c.statement_copy(cobj))

    @classmethod
    def from_param(cls, obj):
        if type(obj) == Statement:
            return obj

        if type(obj) == tuple:
            if len(obj) != 3 and len(obj) != 4:
                raise ValueError("Bad number of statement fields")

            for i in range(len(obj)):
                if type(obj[i]) != Node:
                    raise TypeError("Bad type for statement field " + i)

            g = obj[3] if len(obj) == 4 else None
            return Statement(obj[0], obj[1], obj[2], g)

        raise TypeError("Bad argument type for Statement: %s" % type(obj))

    def __init__(
        self,
        subject=None,
        predicate=None,
        object=None,
        graph=None,
        cursor=None,
        ptr=None,
    ):
        if type(ptr) == POINTER(Statement):
            self._subject = Node.wrap(c.statement_get_subject(ptr))
            self._predicate = Node.wrap(c.statement_get_predicate(ptr))
            self._object = Node.wrap(c.statement_get_object(ptr))
            self._graph = Node.wrap(c.statement_get_graph(ptr))
            self._cursor = None
        elif subject and predicate and object:
            self._subject = subject
            self._predicate = predicate
            self._object = object
            self._graph = graph
            self._cursor = cursor
        else:
            raise TypeError("Missing field for Statement()")

        self.cobj = c.statement_new(
            self._subject.node,
            self._predicate.node,
            self._object.node,
            self._graph.node if self._graph else None,
            self._cursor.cursor if self._cursor else None,
        )

    def __del__(self):
        c.statement_free(self.cobj)
        self.cobj = None

    def __eq__(self, rhs):
        return type(rhs) == Statement and c.statement_equals(
            self.cobj, rhs.cobj
        )

    def __str__(self):
        return " ".join(
            [
                repr(self.subject()),
                repr(self.predicate()),
                repr(self.object()),
                repr(self.graph()),
            ]
        )

    def __repr__(self):
        # FIXME
        return self.__str__()

    def matches(self, s, p, o, g=None):
        return c.statement_matches(
            self.cobj,
            s.node if s is not None else None,
            p.node if p is not None else None,
            o.node if o is not None else None,
            g.node if g is not None else None,
        )

    def node(self, field):
        return Node.wrap(c.statement_get_node(self.cobj, field))

    def subject(self):
        return Node.wrap(c.statement_get_subject(self.cobj))

    def predicate(self):
        return Node.wrap(c.statement_get_predicate(self.cobj))

    def object(self):
        return Node.wrap(c.statement_get_object(self.cobj))

    def graph(self):
        return Node.wrap(c.statement_get_graph(self.cobj))

    def cursor(self):
        return Cursor.wrap(c.statement_get_cursor(self.cobj))


class Iter(Structure):
    @classmethod
    def manage(cls, cobj):
        assert iter is None or type(cobj) == P(Iter)
        return Iter(cobj) if cobj else None

    @classmethod
    def wrap(cls, cobj):
        return Iter.manage(c.iter_copy(cobj))

    def __init__(self, arg):
        self._is_end = False
        if type(arg) == P(Iter):
            self.cobj = arg
        elif type(arg) == Iter:
            self.cobj = c.iter_copy(arg.cobj)
        else:
            raise TypeError("Bad argument type for Iter(): %s" % type(arg))

    def __del__(self):
        c.iter_free(self.cobj)
        self.cobj = None

    def __eq__(self, rhs):
        return type(rhs) == Iter and c.iter_equals(self.cobj, rhs.cobj)

    def __next__(self):
        """Move to and return the next item."""
        if self._is_end:
            raise StopIteration

        item = c.iter_get(self.cobj)
        self._is_end = c.iter_next(self.cobj)

        return Statement.wrap(item)

    def get(self):
        """Get the current item."""
        return Statement.wrap(c.iter_get(self.cobj))


class Range(Structure):
    @classmethod
    def manage(cls, cobj):
        assert range is None or type(cobj) == P(Range)
        return Range(cobj) if cobj else None

    @classmethod
    def wrap(cls, cobj):
        return Range.manage(c.range_copy(cobj))

    def __init__(self, arg):
        if type(arg) == P(Range):
            self.cobj = arg
        elif type(arg) == Range:
            self.cobj = c.range_copy(arg.cobj)
        else:
            raise TypeError("Bad argument type for Range(): %s" % type(arg))

    def __del__(self):
        c.range_free(self.cobj)
        self.cobj = None

    def __eq__(self, rhs):
        return type(rhs) == Range and c.range_equals(self.cobj, rhs.cobj)

    def __iter__(self):
        return Iter.wrap(c.range_begin(self.cobj))

    def front(self):
        return Statement.wrap(c.range_front(self.cobj))

    def empty(self):
        return c.range_empty(self.cobj)

    def begin(self):
        return Iter.wrap(c.range_begin(self.cobj))

    def end(self):
        return Iter.wrap(c.range_end(self.cobj))


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
            self.name_node = arg
            self.cursor = c.cursor_new(self.name_node.node, line, col)
        elif type(arg) == str:
            self.name_node = Node.string(arg)
            self.cursor = c.cursor_new(self.name_node.node, line, col)
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


class Sink(Structure):
    def __init__(self, cobj=None):
        if cobj:
            assert type(cobj) == P(Sink)
            self.cobj = cobj
        else:
            self.env = Env()
            self.cobj = c.sink_new(py_object(self), FreeFunc(), self.env.cobj)

            c.sink_set_base_func(self.cobj, Sink._c_on_base)
            c.sink_set_prefix_func(self.cobj, Sink._c_on_prefix)
            c.sink_set_statement_func(self.cobj, Sink._c_on_statement)
            c.sink_set_end_func(self.cobj, Sink._c_on_end)

    def on_base(self, uri):
        return Status.SUCCESS

    def on_prefix(self, name, uri):
        return Status.SUCCESS

    def on_statement(self, flags, statement):
        return Status.SUCCESS

    def on_end(self, node):
        return Status.SUCCESS

    @staticmethod
    @CFUNCTYPE(c_uint, c_void_p, POINTER(Node))
    def _c_on_base(handle, uri):
        self = cast(handle, py_object).value
        return self.on_base(Node.wrap(uri))

    @staticmethod
    @CFUNCTYPE(c_uint, c_void_p, POINTER(Node), POINTER(Node))
    def _c_on_prefix(handle, name, uri):
        self = cast(handle, py_object).value
        return self.on_prefix(Node.wrap(name), Node.wrap(uri))

    @staticmethod
    @CFUNCTYPE(c_uint, c_void_p, c_uint, POINTER(Statement))
    def _c_on_statement(handle, flags, statement):
        self = cast(handle, py_object).value
        return self.on_statement(flags, Statement.wrap(statement))

    @staticmethod
    @CFUNCTYPE(c_uint, c_void_p, POINTER(Node))
    def _c_on_end(handle, node):
        self = cast(handle, py_object).value
        return self.on_end(Node.wrap(node))


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

# String Utilities
_cfunc("strerror", c_char_p, c_uint)
_cfunc("strlen", c_size_t, String, POINTER(c_uint))
_cfunc("strtod", c_double, String, POINTER(c_size_t))

# Base64
_cfunc("base64_encoded_length", c_size_t, c_size_t, c_bool)
_cfunc("base64_decoded_size", c_size_t, c_size_t)
_cfunc("base64_encode", c_bool, c_char_p, c_void_p, c_size_t, c_bool)
_cfunc("base64_decode", Status, c_void_p, P(c_size_t), String, c_size_t)

# Syntax Utilities
_cfunc("syntax_by_name", Syntax, String)
_cfunc("guess_syntax", Syntax, String)
_cfunc("syntax_has_graphs", c_bool, c_uint)

# URI
# _cfunc("file_uri_parse", c_char_p, String, P(c_char_p))
# _cfunc("uri_string_has_scheme", c_bool, String)
# _cfunc("uri_parse", Status, String, P(URI))
# _cfunc("uri_resolve", None, P(URI), P(URI), P(URI))
# _cfunc("uri_serialise", c_size_t, P(URI), WriteFunc, c_void_p)
# _cfunc(
#     "uri_serialise_relative",
#     c_size_t,
#     P(URI),
#     P(URI),
#     P(URI),
#     WriteFunc,
#     c_void_p,
# )

# World
_cfunc("world_new", P(World))
_cfunc("world_free", None, P(World))
_cfunc("world_get_nodes", P(Nodes), P(World))
_cfunc("world_get_blank", P(Node), P(World))

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
_cfunc("node_free", None, P(Node))

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

FreeFunc = CFUNCTYPE(None, c_void_p)
BaseFunc = CFUNCTYPE(c_uint, c_void_p, P(Node))
PrefixFunc = CFUNCTYPE(c_uint, c_void_p, P(Node), P(Node))
StatementFunc = CFUNCTYPE(c_uint, c_void_p, c_uint, P(Statement))
EndFunc = CFUNCTYPE(c_uint, c_void_p, P(Node))

# Sink
_cfunc("sink_new", P(Sink), ctypes.py_object, FreeFunc, P(Env))
_cfunc("sink_free", None, P(Sink))
# _cfunc("sink_get_env", P(Env), P(Sink))
_cfunc("sink_set_base_func", Status, P(Sink), BaseFunc)
_cfunc("sink_set_prefix_func", Status, P(Sink), PrefixFunc)
_cfunc("sink_set_statement_func", Status, P(Sink), StatementFunc)
_cfunc("sink_set_end_func", Status, P(Sink), EndFunc)

# Reader
_cfunc("reader_new", P(Reader), P(World), c_uint, c_uint, P(Sink), c_size_t)
_cfunc("reader_free", None, P(Reader))
_cfunc("reader_add_blank_prefix", None, P(Reader), String)
_cfunc("reader_start_file", Status, P(Reader), String, c_bool)
# _cfunc("reader_start_stream", Status, P(Reader))
_cfunc("reader_start_string", Status, P(Reader), String, P(Node))
_cfunc("reader_read_chunk", Status, P(Reader))
_cfunc("reader_read_document", Status, P(Reader))
_cfunc("reader_finish", Status, P(Reader))

# Model

_cfunc("model_new", P(Model), P(World), c_uint)
_cfunc("model_copy", P(Model), P(Model))
_cfunc("model_equals", c_bool, P(Model), P(Model))
_cfunc("model_free", None, P(Model))
_cfunc("model_get_world", P(World), P(Model))
_cfunc("model_get_flags", c_uint, P(Model))
_cfunc("model_size", c_size_t, P(Model))
_cfunc("model_empty", c_bool, P(Model))
_cfunc("model_begin", P(Iter), P(Model))
_cfunc("model_end", P(Iter), P(Model))
_cfunc("model_all", P(Range), P(Model))
_cfunc("model_find", P(Iter), P(Model), P(Node), P(Node), P(Node), P(Node))
_cfunc("model_range", P(Range), P(Model), P(Node), P(Node), P(Node), P(Node))
_cfunc("model_get", P(Node), P(Model), P(Node), P(Node), P(Node), P(Node))

_cfunc(
    "model_get_statement",
    P(Statement),
    P(Model),
    P(Node),
    P(Node),
    P(Node),
    P(Node),
)

_cfunc("model_ask", c_bool, P(Model), P(Node), P(Node), P(Node), P(Node))
_cfunc("model_count", c_size_t, P(Model), P(Node), P(Node), P(Node), P(Node))
_cfunc("model_add", Status, P(Model), P(Node), P(Node), P(Node), P(Node))
_cfunc("model_insert", Status, P(Model), P(Statement))
_cfunc("model_add_range", Status, P(Model), P(Range))
_cfunc("model_erase", Status, P(Model), P(Iter))
_cfunc("model_erase_range", Status, P(Model), P(Range))
_cfunc("validate", Status, P(Model))

# Inserter
_cfunc("inserter_new", P(Inserter), P(Model), P(Env), P(Node))
_cfunc("inserter_free", None, P(Inserter))
_cfunc("inserter_get_sink", P(Sink), P(Inserter))

# Statement

_cfunc(
    "statement_new", P(Statement), P(Node), P(Node), P(Node), P(Node), P(Cursor)
)

_cfunc("statement_copy", P(Statement), P(Statement))
_cfunc("statement_free", None, P(Statement))
_cfunc("statement_get_node", P(Node), P(Statement), c_uint)
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

# Iter
_cfunc("iter_copy", P(Iter), P(Iter))
_cfunc("iter_get", P(Statement), P(Iter))
_cfunc("iter_next", c_bool, P(Iter))
_cfunc("iter_equals", c_bool, P(Iter), P(Iter))
_cfunc("iter_free", None, P(Iter))

# Range
_cfunc("range_copy", P(Range), P(Range))
_cfunc("range_free", None, P(Range))
_cfunc("range_front", P(Statement), P(Range))
_cfunc("range_equals", c_bool, P(Range), P(Range))
_cfunc("range_next", c_bool, P(Range))
_cfunc("range_empty", c_bool, P(Range))
_cfunc("range_cbegin", P(Iter), P(Range))
_cfunc("range_cend", P(Iter), P(Range))
_cfunc("range_begin", P(Iter), P(Range))
_cfunc("range_end", P(Iter), P(Range))
# _cfunc("range_serialise", Status, P(Range), P(Sink), c_uint)

# Cursor
_cfunc("cursor_new", P(Cursor), P(Node), c_uint, c_uint)
_cfunc("cursor_copy", P(Cursor), P(Cursor))
_cfunc("cursor_free", None, P(Cursor))
_cfunc("cursor_equals", c_bool, P(Cursor), P(Cursor))
_cfunc("cursor_get_name", P(Node), P(Cursor))
_cfunc("cursor_get_line", c_uint, P(Cursor))
_cfunc("cursor_get_column", c_uint, P(Cursor))
