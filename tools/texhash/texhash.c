/*
 * texhash -- fast content hash of a texture/material identity string.
 *
 * Mirrors the dedup hashing the ingestion pipeline uses to decide whether two
 * scraped texture references point at the same asset. Uses the 64-bit FNV-1a
 * hash: simple, fast, no dependencies, good distribution for short strings.
 *
 * Usage:
 *   texhash "brick_wall_albedo_2k"     # hash one or more args
 *   echo "brick_wall_albedo_2k" | texhash   # hash a line from stdin
 *
 * Output: a 16-hex-digit lowercase hash per input, e.g.
 *   8a9f3c2b1d0e4f56  brick_wall_albedo_2k
 *
 * Build: see Makefile (cc -std=c11 -Wall -Wextra).
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/* FNV-1a 64-bit constants (see http://www.isthe.com/chongo/tech/comp/fnv/). */
#define FNV64_OFFSET_BASIS 0xcbf29ce484222325ULL
#define FNV64_PRIME        0x00000100000001b3ULL

/* Compute the FNV-1a 64-bit hash of `len` bytes at `data`. */
uint64_t texhash_fnv1a(const char *data, size_t len) {
    uint64_t hash = FNV64_OFFSET_BASIS;
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint64_t)(unsigned char)data[i];
        hash *= FNV64_PRIME;
    }
    return hash;
}

/* Print "<16-hex-hash>  <label>" for one input string. */
static void emit(const char *s) {
    uint64_t h = texhash_fnv1a(s, strlen(s));
    printf("%016llx  %s\n", (unsigned long long)h, s);
}

int main(int argc, char **argv) {
    if (argc > 1) {
        /* Hash each command-line argument. */
        for (int i = 1; i < argc; i++) {
            emit(argv[i]);
        }
        return 0;
    }

    /* No args: hash each non-empty line from stdin (trim trailing newline). */
    char *line = NULL;
    size_t cap = 0;
    ssize_t n;
    int any = 0;
    while ((n = getline(&line, &cap, stdin)) != -1) {
        while (n > 0 && (line[n - 1] == '\n' || line[n - 1] == '\r')) {
            line[--n] = '\0';
        }
        if (n == 0) {
            continue; /* skip blank lines */
        }
        emit(line);
        any = 1;
    }
    free(line);

    if (!any) {
        fprintf(stderr, "texhash: no input (pass strings as args or via stdin)\n");
        return 1;
    }
    return 0;
}
