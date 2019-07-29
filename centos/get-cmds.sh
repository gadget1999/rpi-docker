#!/bin/bash

cd /tmp
wget https://github.com/gadget1999/linux/archive/master.zip
unzip master.zip
cp -R /tmp/linux-master/scripts/* /usr/local/bin/
chmod +x /usr/local/bin/*
ls -l /usr/local/bin
rm -R /tmp/linux-master
rm /tmp/master.zip
