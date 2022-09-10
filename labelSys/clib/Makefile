BIN_PTH := ../bin

# Windows
ifeq ($(OS),Windows_NT)
DLLEXT := .dll
always:
	clang -Wall -O2 contour2Mask.c -shared -o $(BIN_PTH)/contour2Mask$(DLLEXT)
	clang -Wall -O2 mergeMasks.c -shared -o $(BIN_PTH)/mergeMasks$(DLLEXT)

else
# Linux or mac
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
	DLLEXT := .so
endif
ifeq ($(UNAME_S),Darwin)
	DLLEXT := .dylib
endif
always:
	cc -fPIC -Wall -O2 contour2Mask.c -shared -o $(BIN_PTH)/contour2Mask$(DLLEXT)
	cc -fPIC -Wall -O2 mergeMasks.c -shared -o $(BIN_PTH)/mergeMasks$(DLLEXT)
endif

