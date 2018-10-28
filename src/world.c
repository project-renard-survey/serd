/*
  Copyright 2011-2018 David Robillard <http://drobilla.net>

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

#define _POSIX_C_SOURCE 200809L /* for posix_fadvise */

#include "world.h"

#include "cursor.h"
#include "node.h"
#include "serd_config.h"
#include "serd_internal.h"

#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if defined(HAVE_POSIX_FADVISE) || defined(HAVE_FILENO)
#   include <fcntl.h>
#endif

#define BLANK_CHARS 11

FILE*
serd_world_fopen(SerdWorld* world, const char* path, const char* mode)
{
	FILE* fd = fopen(path, mode);
	if (!fd) {
		serd_world_errorf(world, SERD_ERR_INTERNAL,
		                  "failed to open file %s (%s)\n",
		                  path, strerror(errno));
		return NULL;
	}
#if defined(HAVE_POSIX_FADVISE) && defined(HAVE_FILENO)
	posix_fadvise(fileno(fd), 0, 0, POSIX_FADV_SEQUENTIAL);
#endif
	return fd;
}

SerdStatus
serd_world_error(const SerdWorld* world, const SerdError* e)
{
	if (world->error_sink) {
		world->error_sink(world->error_handle, e);
	} else {
		fprintf(stderr, "error: ");
		if (e->cursor) {
			fprintf(stderr,
			        "%s:%u:%u: ",
			        serd_node_get_string(e->cursor->file),
			        e->cursor->line,
			        e->cursor->col);
		}
		vfprintf(stderr, e->fmt, *e->args);
	}
	return e->status;
}

SerdStatus
serd_world_errorf(const SerdWorld* world, SerdStatus st, const char* fmt, ...)
{
	va_list args;
	va_start(args, fmt);
	const SerdError e = { st, NULL, fmt, &args };
	serd_world_error(world, &e);
	va_end(args);
	return st;
}

SerdWorld*
serd_world_new(void)
{
	SerdWorld* world = (SerdWorld*)calloc(1, sizeof(SerdWorld));
	SerdNodes* nodes = serd_nodes_new();

	world->rdf_first   = serd_nodes_manage(nodes, serd_new_uri(NS_RDF "first"));
	world->rdf_nil     = serd_nodes_manage(nodes, serd_new_uri(NS_RDF "nil"));
	world->rdf_rest    = serd_nodes_manage(nodes, serd_new_uri(NS_RDF "rest"));
	world->rdf_type    = serd_nodes_manage(nodes, serd_new_uri(NS_RDF "type"));
	world->xsd_boolean = serd_nodes_manage(nodes, serd_new_uri(NS_XSD "boolean"));
	world->xsd_decimal = serd_nodes_manage(nodes, serd_new_uri(NS_XSD "decimal"));
	world->xsd_integer = serd_nodes_manage(nodes, serd_new_uri(NS_XSD "integer"));

	world->blank_node = serd_new_blank("b0000000000");
	world->nodes      = nodes;

	return world;
}

void
serd_world_free(SerdWorld* world)
{
	serd_node_free(world->blank_node);
	serd_nodes_free(world->nodes);
	free(world);
}

const SerdNode*
serd_world_get_blank(SerdWorld* world)
{
	char* buf = serd_node_buffer(world->blank_node);
	memset(buf, 0, BLANK_CHARS + 1);
	world->blank_node->n_bytes = snprintf(
		buf, BLANK_CHARS, "b%u", ++world->next_blank_id);
	return world->blank_node;
}

void
serd_world_set_error_sink(SerdWorld*    world,
                          SerdErrorSink error_sink,
                          void*         handle)
{
	world->error_sink   = error_sink;
	world->error_handle = handle;
}
