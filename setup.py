#+
# Distutils script to install anim_framework. Invoke from the command line
# in this directory as follows:
#
#     python3 setup.py build
#     sudo python3 setup.py install
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import distutils.core

distutils.core.setup \
  (
    name = "anim_framework",
    version = "0.7",
    description = "framework for scripted animations, for Python 3.2 or later",
    author = "Lawrence D'Oliveiro",
    author_email = "ldo@geek-central.gen.nz",
    url = "http://github.com/ldo/anim_framework",
    packages = ["anim"],
  )
