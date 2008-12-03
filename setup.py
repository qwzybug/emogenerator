from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

setup(
	name = 'emogenerator',
	version = '0.1dev',

# 	install_requires = ['genshi >= 0.5'], # 'pyobjc',
# 	install_requires = ['genshi >= 0.5', 'pyobjc'],
	packages = find_packages(exclude = [ 'ez_setup', 'tests' ]),
	package_data = { '': ['templates/*.genshi'] },
	include_package_data = True,
	scripts = ['scripts/emogenerator'],
	zip_safe = True,

	author = 'Jonathan Wight',
	author_email = 'jwight@mqc.com',
	classifiers = [
		'Development Status :: 3 - Alpha',
		'Environment :: MacOS X :: Cocoa',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: BSD License',
		'Operating System :: MacOS :: MacOS X',
		'Programming Language :: Objective C',
		'Topic :: Database',
		'Topic :: Software Development :: Build Tools',
		],
	description = 'Estranged Managed Object Generator',
	license = 'BSD License',
	long_description = file('README.txt').read(),
	platform = 'Mac OS X',
	url = 'http://toxicsoftware.com/link/emogenerator',

# 	entry_points={
# 	'console_scripts': ['vkr = virtualkeyring:main'],
# 	'setuptools.installation': [
# 	'eggsecutable = virtualkeyring:main'],
# 	},
	)

