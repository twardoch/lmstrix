#!/usr/bin/env bash
cd "$(dirname "$0")"

fd -e py -x uvx autoflake -i {}
fd -e py -x uvx pyupgrade --py312-plus {}
fd -e py -x uvx ruff check --output-format=github --fix --unsafe-fixes {}
fd -e py -x uvx ruff format --respect-gitignore --target-version py312 {}
llms . "llms.txt"
hatch clean
gitnextver
hatch build
hatch publish
