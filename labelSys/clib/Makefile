ifeq ($(OS),Windows_NT)
    DLLEXT := .dll
else
	UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
		DLLEXT := .so
    endif
    ifeq ($(UNAME_S),Darwin)
		DLLEXT := .dylib
    endif
endif

always:
	cc -fPIC -Wall -O2 contour2Mask.c -shared -o contour2Mask$(DLLEXT)
	cc -fPIC -Wall -O2 mergeMasks.c -shared -o mergeMasks$(DLLEXT)
