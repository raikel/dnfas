#!/usr/bin/env bash
mkdir -p storage/data/models
cd storage/data/models/
wget -O weights_detector.pth "https://www.dropbox.com/s/z4l7rasz0ydjt9f/weights_detector.pth?dl=0"
wget -O weights_encoder.pth "https://www.dropbox.com/s/6a3eztge2ghci3q/weights_encoder.pth?dl=0"
wget -O weights_marker.npy "https://www.dropbox.com/s/2ne3ronmdqgxsca/weights_marker.npy?dl=0"