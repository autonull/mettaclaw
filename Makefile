# MeTTaClaw — common tasks
# Usage: make build, make run, make dry-run, etc.

.PHONY: build run verbose dry-run shell reset-history clean status help

help:
	@./run.sh -h

build:
	@./run.sh build

run:
	@./run.sh run

verbose:
	@./run.sh verbose

dry-run:
	@./run.sh dry-run

shell:
	@./run.sh shell

reset-history:
	@./run.sh reset-history

clean:
	@./run.sh clean

status:
	@./run.sh status
