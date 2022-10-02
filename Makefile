SRC_PTH := labelSys/clib
BIN_PTH := labelSys/bin

# Windows
ifeq ($(OS),Windows_NT)
DLLEXT := .dll

# Starting of the complie line
CC_PARTIAL := clang

else
# Linux or mac
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
	DLLEXT := .so
endif
ifeq ($(UNAME_S),Darwin)
	DLLEXT := .dylib
endif

# Starting of the complie line
CC_PARTIAL := cc -fPIC

endif

always:
	$(CC_PARTIAL) -Wall -O2 $(SRC_PTH)/contour2Mask.c -shared -o $(BIN_PTH)/contour2Mask$(DLLEXT)
	$(CC_PARTIAL) -Wall -O2 $(SRC_PTH)/mergeMasks.c -shared -o $(BIN_PTH)/mergeMasks$(DLLEXT)
	$(CC_PARTIAL) -Wall -O2 $(SRC_PTH)/b64enc.c -shared -lm -o $(BIN_PTH)/b64enc$(DLLEXT)
