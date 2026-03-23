PYTHON ?= python

all:
	$(PYTHON) setup.py build_ext --inplace

