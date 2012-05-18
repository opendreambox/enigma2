from Screens.ChannelSelection import service_types_tv, service_types_radio
from enigma import eServiceCenter, eServiceReference, iServiceInformation
from ServiceReference import ServiceReference
from Tools.Transponder import ConvertToHumanReadable

def getServiceList(ref):
	print "getServiceList:", type(ref)
	root = eServiceReference(str(ref))
	serviceHandler = eServiceCenter.getInstance()
	return serviceHandler.list(root).getContent("SN", True)

def getAllServices():
	return getServiceList("1:7:1:0:0:0:0:0:0:0:")

def getTVServices():
	return getServiceList(service_types_tv)
	#return getServiceList(service_types_tv + ' ORDER BY name')

def getRadioServices():
	return getServiceList(service_types_radio)
	#return getServiceList(service_types_radio + ' ORDER BY name')

def getTVProviders():
	return getServiceList(service_types_tv + ' FROM PROVIDERS ORDER BY name')

def getRadioProviders():
	return getServiceList(service_types_radio + ' FROM PROVIDERS ORDER BY name')

def getTVSatellites():
	return getServiceList(service_types_tv + ' FROM SATELLITES ORDER BY satellitePosition')

def getTVBouquets():
	return getServiceList(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')

def getRadioBouquets():
	return getServiceList(service_types_radio + ' FROM BOUQUET "bouquets.radio" ORDER BY bouquet')

def getServiceInfoValue(info, serviceref, what):
	v = info.getInfo(serviceref, what)
	if v == -2:
		v = info.getInfoString(what)
	elif v == -1:
		v = "N/A"

	return v

def getServiceName(ref):
	serviceref = ServiceReference(str(ref))
	return serviceref.getServiceName()

def getServicePIDs(ref):
	""" PIDs are only available, if the service was tuned already in the current enigma2 session.
	"""
	serviceref = ServiceReference(str(ref))
	info = serviceref.info()
	data = {}
	if info is None:
		return data
	data["vpid"] = getServiceInfoValue(info, serviceref.ref, iServiceInformation.sVideoPID)
	data["apid"] = getServiceInfoValue(info, serviceref.ref, iServiceInformation.sAudioPID)
	data["pcrpid"] = getServiceInfoValue(info, serviceref.ref, iServiceInformation.sPCRPID)
	data["pmtpid"] = getServiceInfoValue(info, serviceref.ref, iServiceInformation.sPMTPID)
	data["txtpid"] = getServiceInfoValue(info, serviceref.ref, iServiceInformation.sTXTPID)
	data["tsid"] = serviceref.ref.getUnsignedData(2)
	data["onid"] = serviceref.ref.getUnsignedData(3)
	data["sid"] = serviceref.ref.getUnsignedData(1)
	data["namespace"] = serviceref.ref.getUnsignedData(4)
	
	return data

def getTransponderInfo(ref):
	serviceref = ServiceReference(str(ref))
#	print "serviceref:", serviceref
	info = serviceref.info()
	data = {}
	if info is None:
		return data
	transponder_info = info.getInfoObject(serviceref.ref, iServiceInformation.sTransponderData)
	if transponder_info is None:
		return data
	transponder_info["tsid"] = serviceref.ref.getUnsignedData(2)
	transponder_info["onid"] = serviceref.ref.getUnsignedData(3)
	transponder_info["namespace"] = serviceref.ref.getUnsignedData(4)
	return transponder_info

def convertTransponderInfoHumanReadable(transponder_info):
	return ConvertToHumanReadable(transponder_info)

def getCurrentService(session):
	return session.nav.getCurrentlyPlayingServiceReference().toString()

def playService(session, serviceref):
	session.nav.playService(eServiceReference(str(serviceref)))
	
def registerAPIs(api):
	api.add_call("enigma2.servicedata.getAllServices", getAllServices, "()", "[(s,s)]")
	api.add_call("enigma2.servicedata.getTVServices", getTVServices, "()", "[(s,s)]")
	api.add_call("enigma2.servicedata.getRadioServices", getRadioServices, "()", "[(s,s)]")
	api.add_call("enigma2.servicedata.getTVProviders", getTVProviders, "()", "[(s,s)]")
	api.add_call("enigma2.servicedata.getRadioProviders", getRadioProviders, "()", "[(s,s)]")
	api.add_call("enigma2.servicedata.getTVBouquets", getTVBouquets, "()", "[(s,s)]")
	api.add_call("enigma2.servicedata.getRadioBouquets", getRadioBouquets, "()", "[(s,s)]")
	api.add_call("enigma2.servicedata.getServiceList", getServiceList, "(s)", "[(s,s)]")
	
	api.add_call("enigma2.servicedata.getServiceName", getServiceName, "(s)", "s")
	api.add_call("enigma2.servicedata.getServicePIDs", getServicePIDs, "(s)", "{s:i}")
	api.add_call("enigma2.servicedata.getTransponderInfo", getTransponderInfo, "(s)", "{s:t}")
	api.add_call("enigma2.servicedata.convertTransponderInfoHumanReadable", convertTransponderInfoHumanReadable, "{s:t}", "{s:t}")
	
	api.add_call("enigma2.servicedata.getCurrentService", getCurrentService, "()", "s", needsSession = True)
	api.add_call("enigma2.servicedata.playService", playService, "(s)", "", needsSession = True)
	
	
	# some demo code
	
#	tvbouquets = getTVBouquets()
#	print "tvbouquets:", tvbouquets 
#	for bouquet in tvbouquets:
#		print "list:", getServiceList(bouquet[0])
#
#	radiobouquets = getRadioBouquets()
#	print "radiobouquets:", radiobouquets 
#	for bouquet in radiobouquets:
#		print "list:", getServiceList(bouquet[0])
#	 
#	print "tv providers:", getTVProviders()
#	
#	print "tv services:", getTVServices()
#	
#	print "service info ZDF:", getServicePIDs("1:0:1:1F4B:319C:13E:820000:0:0:0:")
#	print "service info WDR:", getServicePIDs("1:0:1:6E96:4B1:1:C00000:0:0:0:")
#	ti = getTransponderInfo("1:0:1:6E96:4B1:1:C00000:0:0:0:")
#	print "transponder info WDR:", ti
#	print "transponder info WDR:", convertTransponderInfoHumanReadable(ti)

