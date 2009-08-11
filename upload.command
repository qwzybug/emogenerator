#!/bin/sh

curl -O http://peak.telecommunity.com/dist/ez_setup.py

hg commit -m 'Building release'

python setup.py register sdist upload
