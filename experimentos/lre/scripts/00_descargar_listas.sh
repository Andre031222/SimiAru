#!/bin/sh
set -eu
destino="$(cd "$(dirname "$0")/.." && pwd)/entrada/listas"
base="https://raw.githubusercontent.com/concepticon/concepticon-data/v3.4.0"
mkdir -p "$destino"
for lista in Swadesh-1955-100 Swadesh-1952-200 Tadmor-2009-100 Swadesh-1961-100 Key-2016-1310 Huber-1992-375 Rowe-1954-232 Lastra-1986-381; do
  curl -sfL "$base/concepticondata/conceptlists/$lista.tsv" -o "$destino/$lista.tsv"
done
curl -sfL "$base/concepticondata/conceptlists.tsv" -o "$destino/conceptlists-indice.tsv"
curl -sfL "$base/metadata.json" -o "$destino/metadata-concepticon-data.json"
curl -sfL "$base/.zenodo.json" -o "$destino/zenodo-concepticon-data.json"
shasum -a 256 "$destino"/*.tsv
