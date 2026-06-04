CXX      ?= c++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -O2
BIN       = pbr_pack

.PHONY: all clean test

all: $(BIN)

$(BIN): pbr_pack.cpp
	$(CXX) $(CXXFLAGS) -o $@ pbr_pack.cpp

# Feed a known set of PBR map filenames and assert the manifest classifies and
# groups them correctly: same material slug, all four maps detected, and the
# coverage/missing split is right.
test: $(BIN)
	@echo "== pbr_pack self-test =="
	@out=$$(./$(BIN) rock_albedo.png rock_normal.png rock_rough_2k.jpg rock_ao.png); \
	echo "$$out"; \
	echo "$$out" | grep -q '"material": "rock"'        || { echo "FAIL: material slug"; exit 1; }; \
	echo "$$out" | grep -q '"map_count": 4'            || { echo "FAIL: map_count"; exit 1; }; \
	echo "$$out" | grep -q '"albedo": "rock_albedo.png"'    || { echo "FAIL: albedo"; exit 1; }; \
	echo "$$out" | grep -q '"roughness": "rock_rough_2k.jpg"' || { echo "FAIL: roughness"; exit 1; }; \
	echo "$$out" | grep -q '"missing": \["metallic","height"\]' || { echo "FAIL: missing set"; exit 1; }; \
	echo "PASS  classified 4 maps into material 'rock'"

clean:
	rm -f $(BIN)
