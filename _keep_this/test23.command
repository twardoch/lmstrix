#!/usr/bin/env bash
for p in $(lmstrix list --sort size --show id); do 
	for c in 32767 45055 49151 61439 73727 81919 94207 102399 112639 122879; do
	    echo; echo "--------------------"; echo ">> $p @ $c"
	    lms unload --all
	    lmstrix test "$p" --ctx $c
	done; 
done
