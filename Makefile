# Automatically extract the list of files to document from the directory listing.
PYFILES := $(shell cd python/fqapi && echo [^_]*.py)
PYDOCS := python/fqapi.html $(PYFILES:%.py=python/fqapi.%.html)

doc: $(PYDOCS)

python/fqapi.html: python/fqapi/__init__.py Makefile
	cd python && pydoc -w fqapi

python/fqapi.%.html: python/fqapi/%.py Makefile
	cd python && pydoc -w fqapi.$*
