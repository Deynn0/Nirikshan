.PHONY: test lint dev eval help

help:
	@$(MAKE) -C backend help

test:
	@$(MAKE) -C backend test

lint:
	@$(MAKE) -C backend lint

dev:
	@$(MAKE) -C backend dev

eval:
	@$(MAKE) -C backend eval
