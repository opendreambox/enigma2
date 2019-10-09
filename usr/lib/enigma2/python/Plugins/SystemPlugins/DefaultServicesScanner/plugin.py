#from Components.ActionMap import ActionMap, NumberActionMap
#from Components.Input import Input
#from Components.Ipkg import IpkgComponent
#from Components.Label import Label
#from Components.MenuList import MenuList
#from Components.Slider import Slider
from __future__ import print_function
from Components.NimManager import nimmanager
from Plugins.Plugin import PluginDescriptor
from Screens.ScanSetup import ScanSetup
from Screens.ServiceScan import ServiceScan
from Screens.MessageBox import MessageBox
from Tools.Directories import resolveFilename, SCOPE_CONFIG, copyfile
#from Screens.Screen import Screen
from os import unlink
from enigma import eTimer, eDVBDB
from six.moves import range

class DefaultServiceScan(ServiceScan):
	skin = """
	<screen position="center,120" size="720,520" title="Service Scan">
		<widget source="FrontendInfo" render="Pixmap" pixmap="skin_default/icons/scan-s.png" position="30,20" size="64,64" alphatest="on">
			<convert type="FrontendInfo">TYPE</convert>
			<convert type="ValueRange">0,0</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="FrontendInfo" render="Pixmap" pixmap="skin_default/icons/scan-c.png" position="30,20" size="64,64" alphatest="on">
			<convert type="FrontendInfo">TYPE</convert>
			<convert type="ValueRange">1,1</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="FrontendInfo" render="Pixmap" pixmap="skin_default/icons/scan-t.png" position="30,20" size="64,64" alphatest="on">
			<convert type="FrontendInfo">TYPE</convert>
			<convert type="ValueRange">2,2</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<widget name="network" position="180,30" size="470,26" font="Regular;22"/>
		<widget name="transponder" position="180,60" size="470,26" font="Regular;22"/>
		<widget name="scan_state" position="80,110" zPosition="2" size="560,24" font="Regular;20"/>
		<widget name="pass" position="80,110" size="560,24" font="Regular;20"/>
		<widget name="scan_progress" position="80,160" size="560,15" pixmap="skin_default/progress.png" borderWidth="2" borderColor="#cccccc"/>
		<widget name="servicelist" position="80,200" size="560,300" selectionDisabled="1"/>
	</screen>"""

	def __init__(self, session, scanList):
		try:
			unlink(resolveFilename(SCOPE_CONFIG) + "/lamedb");
		except OSError:
			pass
		db = eDVBDB.getInstance()
		db.reloadServicelist()
		ServiceScan.__init__(self, session, scanList)
		self.timer = eTimer()
		self.timer_conn = self.timer.timeout.connect(self.ok)
		self.timer.start(1000)

class DefaultServicesScannerPlugin(ScanSetup):
	skin = """
		<screen position="center,120" size="720,520" title="Service scan">
			<widget name="config" position="10,10" size="700,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<eLabel	position="10,480" size="700,1" backgroundColor="grey"/>
			<widget name="introduction" position="10,488" size="700,25" font="Regular;22" halign="center" />
		</screen>"""
		
	def __init__(self, session, args = None):
		ScanSetup.__init__(self, session, 'S')
		# backup lamedb
		confdir = resolveFilename(SCOPE_CONFIG)
		copyfile(confdir + "/lamedb", confdir + "/lamedb.backup")
		self.scan_type.value = "multisat"
		self.createSetup()
		self.scanIndex = 0
		self.selectSat(0)
		self.onFirstExecBegin.append(self.runScan)
		
	def selectSat(self, index):
		for satindex in range(len(self.multiscanlist)):
			if satindex != index:
				self.multiscanlist[satindex][1].value = False
			else:
				self.multiscanlist[satindex][1].value = True
				
	def runScan(self):
		print("runScan")
		self.keyGo()

	def startScan(self, tlist, flags, feid):
		print("startScan")
		if len(tlist):
			# flags |= eComponentScan.scanSearchBAT
			self.session.openWithCallback(self.scanFinished, DefaultServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags}])
		else:
			self.session.openWithCallback(self.scanFinished, MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)

	def scanFinished(self, value = None):
		print("finished")
		print("self.scanIndex:", self.scanIndex)
		db = eDVBDB.getInstance()
		print("self.multiscanlist:", self.multiscanlist)
		if len(self.multiscanlist) - 1 >= self.scanIndex and len(self.multiscanlist[self.scanIndex]) > 0:
			satint = self.multiscanlist[self.scanIndex][0]
			print("scanned sat:", satint)
			db.saveServicelist("/tmp/lamedb." + str(satint))
			file = open("/tmp/sat" + str(satint) + ".info", "w")
			xml = """<default>
	<prerequisites>
		<tag type="services" />
		<bcastsystem type="DVB-S" />
		<satellite type="%d" />
	</prerequisites>
	
	<info>
		<author>%s</author>
		<name>%s</name>
	</info>

	<files type="directories">
		<file type="services" name="lamedb.%d">
		</file>
	</files>
</default>""" % (satint, "Dream", nimmanager.getSatDescription(satint), satint)
			file.write(xml)
			file.close()
		
		self.scanIndex += 1
		if self.scanIndex + 1 >= len(self.multiscanlist):
			print("no more sats to scan")
			confdir = resolveFilename(SCOPE_CONFIG)
			copyfile(confdir + "/lamedb.backup", confdir + "/lamedb")
			db.reloadServicelist()
			self.close()
		else:
			self.selectSat(self.scanIndex)
			self.keyGo()

def DefaultServicesScannerMain(session, **kwargs):
	session.open(DefaultServicesScannerPlugin)

def Plugins(**kwargs):
	return PluginDescriptor(name="Default Services Scanner", description=_("Scans default lamedbs sorted by satellite with a connected dish positioner"), where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=DefaultServicesScannerMain)
