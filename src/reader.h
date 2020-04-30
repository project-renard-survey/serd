/*
  Copyright 2011-2017 David Robillard <http://drobilla.net>

  Permission to use, copy, modify, and/or distribute this software for any
  purpose with or without fee is hereby granted, provided that the above
  copyright notice and this permission notice appear in all copies.

  THIS SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
*/

#include "serd_internal.h"

#include <assert.h>
#include <stdio.h>

static inline int
peek_byte(SerdReader* reader)
{
	SerdByteSource* source = &reader->source;

	return source->eof ? EOF : (int)source->read_buf[source->read_head];
}

static inline int
eat_byte(SerdReader* reader)
{
	const int        c  = peek_byte(reader);
	const SerdStatus st = serd_byte_source_advance(&reader->source);
	if (st) {
		reader->status = st;
	}
	return c;
}

static inline int
eat_byte_safe(SerdReader* reader, const int byte)
{
	(void)byte;

	const int c = eat_byte(reader);
	assert(c == byte);
	return c;
}

static inline int
eat_byte_check(SerdReader* reader, const int byte)
{
	const int c = peek_byte(reader);
	if (c != byte) {
		return r_err(reader, SERD_ERR_BAD_SYNTAX,
		             "expected `%c', not `%c'\n", byte, c);
	}
	return eat_byte_safe(reader, byte);
}

static inline bool
eat_string(SerdReader* reader, const char* str, unsigned n)
{
	bool bad = false;
	for (unsigned i = 0; i < n; ++i) {
		bad |= (bool)eat_byte_check(reader, ((const uint8_t*)str)[i]);
	}
	return bad;
}

static inline SerdStatus
push_byte(SerdReader* reader, Ref ref, const int c)
{
	assert(c != EOF);
	SERD_STACK_ASSERT_TOP(reader, ref);

	char* const     s    = serd_stack_push(&reader->stack, 1);
	SerdNode* const node = (SerdNode*)(reader->stack.buf + ref);
	++node->n_bytes;
	*(s - 1) = (uint8_t)c;
	*s       = '\0';
	return SERD_SUCCESS;
}

static inline void
push_bytes(SerdReader* reader, Ref ref, const uint8_t* bytes, unsigned len)
{
	for (unsigned i = 0; i < len; ++i) {
		push_byte(reader, ref, bytes[i]);
	}
}
