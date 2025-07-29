#!/usr/bin/env bash
lmstrix scan
for p in $(lmstrix list --sort smart --show id); do
	echo
	echo "--------------------"
	echo ">> $p"
	lms unload --all
	lmstrix test "$p"
done
