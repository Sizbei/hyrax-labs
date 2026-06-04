CC      ?= cc
CFLAGS  ?= -std=c11 -Wall -Wextra -O2
BIN      = texhash

.PHONY: all clean test

all: $(BIN)

$(BIN): texhash.c
	$(CC) $(CFLAGS) -o $@ texhash.c

# Assert a known input -> hash. "test" has the canonical FNV-1a 64-bit value
# f9e6e6ef197c2b25 (matches the published FNV reference vectors), proving the
# implementation is correct.
test: $(BIN)
	@echo "== texhash self-test =="
	@got=$$(printf '%s' "test" | ./$(BIN) | awk '{print $$1}'); \
	want="f9e6e6ef197c2b25"; \
	if [ "$$got" = "$$want" ]; then \
		echo "PASS  FNV-1a(\"test\") = $$got"; \
	else \
		echo "FAIL  FNV-1a(\"test\") = $$got (expected $$want)"; \
		exit 1; \
	fi
	@got2=$$(./$(BIN) "brick_wall_albedo_2k" | awk '{print $$1}'); \
	if [ -n "$$got2" ] && [ $${#got2} -eq 16 ]; then \
		echo "PASS  16-hex hash for material id: $$got2"; \
	else \
		echo "FAIL  unexpected hash output: $$got2"; \
		exit 1; \
	fi

clean:
	rm -f $(BIN)
