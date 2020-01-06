#!/usr/bin/env bash
WEIGHTS_DETECTOR=weights_detector.pth
WEIGHTS_ENCODER=weights_encoder.pth
WEIGHTS_MARKER=weights_marker.npy
mkdir -p storage/data/models
cd storage/data/models/

if [[ ! -f "$WEIGHTS_DETECTOR" ]]; then
    wget -O ${WEIGHTS_DETECTOR} "https://www.dropbox.com/s/z4l7rasz0ydjt9f/weights_detector.pth?dl=0"
fi

if [[ ! -f "$WEIGHTS_ENCODER" ]]; then
    wget -O ${WEIGHTS_ENCODER} "https://www.dropbox.com/s/6a3eztge2ghci3q/weights_encoder.pth?dl=0"
fi

if [[ ! -f "$WEIGHTS_MARKER" ]]; then
    wget -O ${WEIGHTS_MARKER} "https://www.dropbox.com/s/2ne3ronmdqgxsca/weights_marker.npy?dl=0"
fi