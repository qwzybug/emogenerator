emogenerator
============

:author: Jonathan Wight <jwight@mac.com>
:description: Estranged Managed Object Generator


Goal
----
Python tool to generate Objective-C wrappers for CoreData object models. emogenerator is inspired by Jonathan "Wolf" Rentzsch's mogenerator_ tool.

emogenerator also uses special comment 'guard' sections in the generated code to allow you to mix and match your code with auto-generated code. emogenerator also uses a mature and well maintained template system (genshi_) to generate Objective-C source.

.. _mogenerator: http://rentzsch.com/code/mogenerator
.. _genshi: http://genshi.edgewall.org/

Install
-------

With setuptools_::

  $ easy_install -U emogenerator

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools


Usage
-----

In a directory containing a CoreData .xcdatamodel (or .xcdatamodeld) file:

 Usage: emogenerator [options] [INPUT]

 Options:
   --version             show program's version number and exit
   -h, --help            show this help message and exit
   --momc=MOMC           The momc compiler program to use when converting
                         xcdatamodel files to mom files (default:
                         '/Developer/usr/bin/momc')
   -i INPUT, --input=INPUT
                         The input xcdatamodel or mom file (type is inferred by
                         file extension).
   -o OUTPUT, --output=OUTPUT
                         Output directory for generated files.
   -t TEMPLATE, --template=TEMPLATE
                         Directory containing templates.
   -c CONFIG, --config=CONFIG
                         Path to config plist file (values will be passed to
                         template engine as a dictionary)
   -v, --verbose         set the log level to INFO
   --loglevel=LOGLEVEL   set the log level, 0 = no log, 10+ = level of logging
   --logfile=LOG_FILE    File to log messages to. If - or not provided then
                         stdout is used.
