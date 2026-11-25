#!/bin/bash
# Doppelklick startet die Weboberfläche des Tabulariums im Browser.
cd "$(dirname "$0")"
clear
python3 tabularium.py web
