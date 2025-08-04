#!/usr/bin/env bash
cd "$(dirname "$0")" || exit

fd -e py -x uvx autoflake -i {} &>cleanup.txt
fd -e py -x uvx pyupgrade --py312-plus {} &>>cleanup.txt
fd -e py -x uvx ruff check --output-format=github --fix --unsafe-fixes {} &>>cleanup.txt
fd -e py -x uvx ruff format --respect-gitignore --target-version py312 {} &>>cleanup.txt
llms . "llms.txt"
uvx hatch clean
gitnextvers .
uvx hatch build
uvx hatch publish
