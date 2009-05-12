#!/usr/bin/env python

import commands
import datetime
import glob
import logging
import optparse
import os
import pkg_resources
import re
import subprocess
import sys
import tempfile

import CoreData
import Foundation

import genshi.template

def main(args):
	def store_open_file(option, opt_str, value, parser, *args, **kwargs):
		if value == '-':
			theFile = option.default
		else:
			theFile = file(value, kwargs['mode'])
		setattr(parser.values, option.dest, theFile)

	theUsage = '''%prog [options] [INPUT]'''
	theVersion = '%prog 0.1.5'

	# If no explicit path to momc is set ask 'which' for it.
	theDefaultMomcPath = None
	theResult, thePath = commands.getstatusoutput('which momc')
	if theResult == 0:
		theDefaultMomcPath = thePath

	# If still no momc then look in the known places.
	if theDefaultMomcPath == None:
		theMomPaths = [
			'/Library/Application Support/Apple/Developer Tools/Plug-ins/XDCoreDataModel.xdplugin/Contents/Resources/momc',
			'/Developer/Library/Xcode/Plug-ins/XDCoreDataModel.xdplugin/Contents/Resources/momc',
			]
		for thePath in theMomPaths:
			if os.path.exists(thePath):
				theDefaultMomcPath = thePath
				break

	theDefaultTemplateDirectory = pkg_resources.resource_filename('emogenerator', 'templates')

	parser = optparse.OptionParser(usage=theUsage, version=theVersion)
	parser.add_option('', '--momc', action='store', dest='momcpath', type='string', metavar='MOMC', default = theDefaultMomcPath,
		help='The momc compiler program to use when converting xcdatamodel files to mom files (default: \'%s\')' % theDefaultMomcPath)
	parser.add_option('-i', '--input', action='store', dest='input', type='string', metavar='INPUT',
		help='The input xcdatamodel or mom file (type is inferred by file extension).')
	parser.add_option('-o', '--output', action='store', dest='output', type='string', default = '', metavar='OUTPUT',
		help='Output directory for generated files.')
	parser.add_option('-t', '--template', action='store', dest='template', type='string', default = theDefaultTemplateDirectory, metavar='TEMPLATE',
		help='Directory containing templates (default: \'%s\'' % theDefaultTemplateDirectory)
	parser.add_option('-c', '--config', action='store', dest='config', type='string', metavar='CONFIG',
		help='Path to config plist file (values will be passed to template engine as a dictionary)')
	parser.add_option('-v', '--verbose', action='store_const', dest='loglevel', const=logging.INFO, default=logging.WARNING,
		help='set the log level to INFO')
	parser.add_option('', '--loglevel', action='store', dest='loglevel', type='int',
		help='set the log level, 0 = no log, 10+ = level of logging')
	parser.add_option('', '--logfile', action='callback', dest='logstream', type='string', default = sys.stderr, callback=store_open_file, callback_kwargs = {'mode':'w'}, metavar='LOG_FILE',
		help='File to log messages to. If - or not provided then stdout is used.')

	(theOptions, theArguments) = parser.parse_args(args = args[1:])

	logging.basicConfig(level = theOptions.loglevel, format = '%(message)s', stream = theOptions.logstream)

	logging.debug(theOptions)
	logging.debug(theArguments)

	if theOptions.input == None and len(theArguments) > 0:
		theOptions.input = theArguments.pop(0)

	try:
		emogenerator(theOptions, theArguments)
	except Exception, e:
		logging.error('Error: %s' % str(e))
		sys.exit(1)

def emogenerator(options, inArguments):
	# If we don't have an input file lets try and find one in the cwd
	if options.input == None:
		files = glob.glob('*.xcdatamodel')
		if files:
			options.input = files[0]
	if options.input == None:
		files = glob.glob('*.xcdatamodeld')
		if files:
			options.input = files[0]
	if options.input == None:
		files = glob.glob('*.mom')
		if files:
			options.input = files[0]
	if options.input == None:
		raise Exception('Could not find a data model file.')

	# If we still don't have an input file we need to bail.
	if not os.path.exists(options.input):
		raise Exception('Input file doesnt exist at %s' % options.input)

	options.input_type = os.path.splitext(options.input)[1][1:]
	if options.input_type not in ['mom', 'xcdatamodel', 'xcdatamodeld']:
		raise Exception('Input file is not a .mom or a .xcdatamodel. Why are you trying to trick me?')

	logging.info('Processing \'%s\'', options.input)

	# Set up a list of CoreData attribute types to Cocoa classes/C types. In theory this could be user configurable, but I don't see the need.
	theTypenamesByAttributeType = {
		CoreData.NSStringAttributeType: dict(cocoaType = 'NSString'),
		CoreData.NSDateAttributeType: dict(cocoaType = 'NSDate'),
		CoreData.NSBinaryDataAttributeType: dict(cocoaType = 'NSData'),
		CoreData.NSDecimalAttributeType: dict(cocoaType = 'NSDecimalNumber'),
		CoreData.NSInteger16AttributeType: dict(cocoaType = 'NSNumber', ctype = 'short', toCTypeConverter = 'shortValue', toCocoaTypeConverter = 'numberWithShort'),
		CoreData.NSInteger32AttributeType: dict(cocoaType = 'NSNumber', ctype = 'int', toCTypeConverter = 'intValue', toCocoaTypeConverter = 'numberWithInt'),
		CoreData.NSInteger64AttributeType: dict(cocoaType = 'NSNumber', ctype = 'long long', toCTypeConverter = 'longLongValue', toCocoaTypeConverter = 'numberWithLongLong'),
		CoreData.NSDoubleAttributeType: dict(cocoaType = 'NSNumber', ctype = 'double', toCTypeConverter = 'doubleValue', toCocoaTypeConverter = 'numberWithDouble'),
		CoreData.NSFloatAttributeType: dict(cocoaType = 'NSNumber', ctype = 'float', toCTypeConverter = 'floatValue', toCocoaTypeConverter = 'numberWithFloat'),
		CoreData.NSBooleanAttributeType: dict(cocoaType = 'NSNumber', ctype = 'BOOL', toCTypeConverter = 'boolValue', toCocoaTypeConverter = 'numberWithBool'),
		}

	if options.input_type in ['xcdatamodel', 'xcdatamodeld']:
		logging.info('Using momc at \'%s\'', options.momcpath)
		# Create a place to put the generated mom file
		theTempDirectory = tempfile.mkdtemp()
		theObjectModelPath = os.path.join(theTempDirectory, 'Output.mom')

		# Tell momc to compile our xcdatamodel into a managed object model
		theResult = subprocess.call([options.momcpath, options.input, theObjectModelPath])
		if theResult != 0:
			raise Exception('momc failed with %d', theResult)
	else:
		theObjectModelPath = options.input

	# No? Ok, let's fall back to the cwd
	if options.template == None:
		options.template = 'templates'

	logging.info('Using input mom file \'%s\'', theObjectModelPath)
	logging.info('Using output directory \'%s\'', options.output)
	logging.info('Using template directory \'%s\'', options.template)

	# Load the managed object model.
	theObjectModelURL = Foundation.NSURL.fileURLWithPath_(theObjectModelPath)
	theObjectModel = CoreData.NSManagedObjectModel.alloc().initWithContentsOfURL_(theObjectModelURL)

	# Start up genshi..
	theLoader = genshi.template.TemplateLoader(options.template)

	theContext = dict(
		C = lambda X:X[0].upper() + X[1:],
		author = Foundation.NSFullUserName(),
		date = datetime.datetime.now().strftime('%x'),
		year = datetime.datetime.now().year,
		organizationName = '__MyCompanyName__',
		options = dict(
			suppressAccessorDeclarations = True,
			),
		)

	theXcodePrefs = Foundation.NSDictionary.dictionaryWithContentsOfFile_(os.path.expanduser('~/Library/Preferences/com.apple.xcode.plist'))
	if theXcodePrefs:
		if 'PBXCustomTemplateMacroDefinitions' in theXcodePrefs:
			if 'ORGANIZATIONNAME' in theXcodePrefs['PBXCustomTemplateMacroDefinitions']:
				theContext['organizationName'] = theXcodePrefs['PBXCustomTemplateMacroDefinitions']['ORGANIZATIONNAME']

	# Process each entity...
	for theEntityDescription in theObjectModel.entities():
		# Create a dictionary describing the entity, we'll be passing this to the genshi template.
		theEntityDict = {
			'entity': theEntityDescription,
			'name': theEntityDescription.name(),
			'className': theEntityDescription.managedObjectClassName(),
			'superClassName': 'NSManagedObject',
			'properties': [],
			'relatedEntityClassNames': [],
			}

		if theEntityDict['className'] == 'NSManagedObject':
			logging.info('Skipping entity \'%s\', no custom subclass specified.', theEntityDescription.name())
			continue

		if theEntityDescription.superentity():
			theEntityDict['superClassName'] = theEntityDescription.superentity().managedObjectClassName()

		# Process each property of the entity.
		for thePropertyDescription in theEntityDescription.properties():
			if theEntityDescription != thePropertyDescription.entity():
				continue

			# This dictionary describes the property and is appended to the entity dictionary we created earlier.
			thePropertyDict = {
				'property': thePropertyDescription,
				'name': thePropertyDescription.name(),
				'type': thePropertyDescription.className(),
				'CType': None,
				}

			if thePropertyDescription.className() == 'NSAttributeDescription':
				if thePropertyDescription.attributeType() not in theTypenamesByAttributeType:
					logging.warning('Did not understand the property type: %d', thePropertyDescription.attributeType())
					continue

				theTypenameByAttributeType = theTypenamesByAttributeType[thePropertyDescription.attributeType()]

				thePropertyDict['CocoaType'] = theTypenameByAttributeType['cocoaType']
				if 'ctype' in theTypenameByAttributeType:
					thePropertyDict['CType'] = theTypenameByAttributeType['ctype']
					thePropertyDict['toCTypeConverter'] = theTypenameByAttributeType['toCTypeConverter']
					thePropertyDict['toCocoaTypeConverter'] = theTypenameByAttributeType['toCocoaTypeConverter']

			elif thePropertyDescription.className() == 'NSRelationshipDescription':
				thePropertyDict['isToMany'] = thePropertyDescription.isToMany()
				thePropertyDict['destinationEntityClassNames'] = thePropertyDescription.destinationEntity().managedObjectClassName()
				theEntityDict['relatedEntityClassNames'].append(thePropertyDescription.destinationEntity().managedObjectClassName())
			else:
				continue

			theEntityDict['properties'].append(thePropertyDict)

		theEntityDict['attributes'] = [x for x in theEntityDict['properties'] if x['type'] == 'NSAttributeDescription']
		theEntityDict['relationships'] = [x for x in theEntityDict['properties'] if x['type'] == 'NSRelationshipDescription']

		theTemplateNames = ['classname.h.genshi', 'classname.m.genshi']
		for theTemplateName in theTemplateNames:

			theTemplate = theLoader.load(theTemplateName, cls=genshi.template.NewTextTemplate)

			theContext['entity'] = theEntityDict

			theStream = theTemplate.generate(**theContext)
			theNewContent = theStream.render()

			theFilename = theEntityDescription.managedObjectClassName() + '.' + re.match(r'.+\.(.+)\.genshi', theTemplateName).group(1)

			theOutputPath = os.path.join(options.output, theFilename)

			if os.path.exists(theOutputPath) == False:
				file(theOutputPath, 'w').write(theNewContent)
			else:
				theCurrentContent = file(theOutputPath).read()
				theNewContent = merge(theNewContent, theCurrentContent, [
					('#pragma mark begin emogenerator accessors', '#pragma mark end emogenerator accessors'),
					('#pragma mark begin emogenerator forward declarations', '#pragma mark end emogenerator forward declarations'),
					])
				if theNewContent != theCurrentContent:
					file(theOutputPath, 'w').write(theNewContent)

def merge(inTemplate, inOriginal, inDelimiters):
	theComponents = []
	for theDelimiter in inDelimiters:
		### Find delimited section in template
		theTemplateStart = inTemplate.find(theDelimiter[0])
		if not theTemplateStart:
			continue
		theTemplateStart += len(theDelimiter[0])
		theTemplateEnd = inTemplate.find(theDelimiter[1], theTemplateStart)
		if not theTemplateEnd:
			continue

		### Find delimited section in original
		theOriginalStart = inOriginal.find(theDelimiter[0])
		if not theOriginalStart:
			continue
		theOriginalStart += len(theDelimiter[0])
		theOriginalEnd = inOriginal.find(theDelimiter[1], theOriginalStart)
		if not theOriginalEnd:
			continue

		inOriginal = inOriginal[:theOriginalStart] + inTemplate[theTemplateStart:theTemplateEnd] + inOriginal[theOriginalEnd:]

	return inOriginal

# if __name__ == '__main__':
# #	main(sys.argv)
# 	os.chdir(os.path.expanduser('~/Desktop/emogenerator/test'))
# 	main(['emogenerator', '-v'])
