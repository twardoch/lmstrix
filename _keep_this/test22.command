#!/usr/bin/env bash
for p in $(lmstrix list --sort size --show id); do
	echo
	echo "--------------------"
	echo ">> $p @ $c"
	lms unload --all
	lmstrix test "$p"
done
