#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import subprocess
import sys

def execute(command):
	s = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = s.communicate()
	print stdout
	print stderr
	return stdout

packages = re.split('[\s]+', sys.argv[1])

command = ['apt-get', 'install'] + packages
execute(command)

