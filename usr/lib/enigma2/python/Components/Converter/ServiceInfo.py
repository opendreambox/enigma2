from __future__ import division
from __future__ import print_function
from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService, iAudioType_ENUMS as iAt, CT_MPEG2, CT_H264, CT_MPEG1, CT_MPEG4_PART2, CT_VC1, CT_VC1_SIMPLE_MAIN, CT_H265, CT_DIVX311, CT_DIVX4, CT_SPARK, CT_VP6, CT_VP8, CT_VP9, CT_H263, CT_MJPEG, CT_REAL, CT_AVS, CT_UNKNOWN
from Components.Element import cached

class ServiceInfo(Converter, object):
	HAS_TELETEXT = 0
	IS_MULTICHANNEL = 1
	IS_CRYPTED = 2
	IS_WIDESCREEN = 3
	SUBSERVICES_AVAILABLE = 4
	XRES = 5
	YRES = 6
	APID = 7
	VPID = 8
	PCRPID = 9
	PMTPID = 10
	TXTPID = 11
	TSID = 12
	ONID = 13
	SID = 14
	FRAMERATE = 15
	TRANSFERBPS = 16
	HAS_SUBTITLES = 17
	IS_HDR = 18
	VIDEO_PARAMS = 19
	VIDEO_TYPE = 20

	def __init__(self, type):
		Converter.__init__(self, type)
		self.type, self.interesting_events = {
				"HasTelext": (self.HAS_TELETEXT, (iPlayableService.evUpdatedInfo,)),
				"IsMultichannel": (self.IS_MULTICHANNEL, (iPlayableService.evUpdatedInfo,)),
				"IsCrypted": (self.IS_CRYPTED, (iPlayableService.evUpdatedInfo,)),
				"IsWidescreen": (self.IS_WIDESCREEN, (iPlayableService.evVideoSizeChanged,)),
				"IsHdr": (self.IS_HDR, (iPlayableService.evVideoSizeChanged,)),
				"SubservicesAvailable": (self.SUBSERVICES_AVAILABLE, (iPlayableService.evUpdatedEventInfo,)),
				"VideoType": (self.VIDEO_TYPE, (iPlayableService.evVideoTypeReady,)),
				"VideoWidth": (self.XRES, (iPlayableService.evVideoSizeChanged,)),
				"VideoHeight": (self.YRES, (iPlayableService.evVideoSizeChanged,)),
				"VideoParams": (self.VIDEO_PARAMS, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoProgressiveChanged, iPlayableService.evVideoFramerateChanged)),
				"AudioPid": (self.APID, (iPlayableService.evUpdatedInfo,)),
				"VideoPid": (self.VPID, (iPlayableService.evUpdatedInfo,)),
				"PcrPid": (self.PCRPID, (iPlayableService.evUpdatedInfo,)),
				"PmtPid": (self.PMTPID, (iPlayableService.evUpdatedInfo,)),
				"TxtPid": (self.TXTPID, (iPlayableService.evUpdatedInfo,)),
				"TsId": (self.TSID, (iPlayableService.evUpdatedInfo,)),
				"OnId": (self.ONID, (iPlayableService.evUpdatedInfo,)),
				"Sid": (self.SID, (iPlayableService.evUpdatedInfo,)),
				"Framerate": (self.FRAMERATE, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoFramerateChanged)),
				"TransferBPS": (self.TRANSFERBPS, (iPlayableService.evUpdatedInfo,)),
				"HasSubtitles": (self.HAS_SUBTITLES, (iPlayableService.evUpdatedInfo,)),
			}[type]
		self.need_wa = iPlayableService.evVideoSizeChanged in self.interesting_events

	def reuse(self):
		self.need_wa = iPlayableService.evVideoSizeChanged in self.interesting_events

	def getServiceInfoString(self, info, what, convert = lambda x: "%d" % x):
		v = info.getInfo(what)
		if v == -1:
			return "N/A"
		if v == -2:
			return info.getInfoString(what)
		return convert(v)

	@cached
	def getBoolean(self):
		service = self.source.service
		if self.type == self.HAS_SUBTITLES:
			subtitle = service and service.subtitleTracks()
			return subtitle and subtitle.getNumberOfSubtitleTracks() > 0

		info = service and service.info()
		if not info:
			return False
		
		if self.type == self.HAS_TELETEXT:
			tpid = info.getInfo(iServiceInformation.sTXTPID)
			return tpid != -1
		elif self.type == self.IS_MULTICHANNEL:
			# FIXME. but currently iAudioTrackInfo doesn't provide more information.
			audio = service.audioTracks()
			if audio:
				n = audio.getNumberOfTracks()
				idx = 0
				while idx < n:
					i = audio.getTrackInfo(idx)
					if i.getType() in (iAt.atAC3, iAt.atDDP, iAt.atDTS, iAt.atDTSHD):
						return True
					idx += 1
			return False
		elif self.type == self.IS_CRYPTED:
			return info.getInfo(iServiceInformation.sIsCrypted) == 1
		elif self.type == self.IS_HDR:
			return info.getInfoString(iServiceInformation.sEotf) in ('SMPTE ST 2084 (HDR10)', 'ARIB STD-B67 (HLG)')
		elif self.type == self.IS_WIDESCREEN:
			return info.getInfo(iServiceInformation.sAspect) in (3, 4, 7, 8, 0xB, 0xC, 0xF, 0x10)
		elif self.type == self.SUBSERVICES_AVAILABLE:
			subservices = service.subServices()
			return subservices and subservices.getNumberOfSubservices() > 0

	boolean = property(getBoolean)
	
	@cached
	def getText(self):
		service = self.source.service
		info = service and service.info()
		if not info:
			return ""

		if self.type == self.XRES:
			return self.getServiceInfoString(info, iServiceInformation.sVideoWidth)
		elif self.type == self.YRES:
			return self.getServiceInfoString(info, iServiceInformation.sVideoHeight)
		elif self.type == self.APID:
			return self.getServiceInfoString(info, iServiceInformation.sAudioPID)
		elif self.type == self.VPID:
			return self.getServiceInfoString(info, iServiceInformation.sVideoPID)
		elif self.type == self.PCRPID:
			return self.getServiceInfoString(info, iServiceInformation.sPCRPID)
		elif self.type == self.PMTPID:
			return self.getServiceInfoString(info, iServiceInformation.sPMTPID)
		elif self.type == self.TXTPID:
			return self.getServiceInfoString(info, iServiceInformation.sTXTPID)
		elif self.type == self.TSID:
			return self.getServiceInfoString(info, iServiceInformation.sTSID)
		elif self.type == self.ONID:
			return self.getServiceInfoString(info, iServiceInformation.sONID)
		elif self.type == self.SID:
			return self.getServiceInfoString(info, iServiceInformation.sSID)
		elif self.type == self.FRAMERATE:
			return self.getServiceInfoString(info, iServiceInformation.sFrameRate, lambda x: "%d fps" % ((x+500)//1000))
		elif self.type == self.TRANSFERBPS:
			return self.getServiceInfoString(info, iServiceInformation.sTransferBPS, lambda x: "%d kB/s" % (x//1024))
		elif self.type == self.VIDEO_PARAMS:
			yres = info.getInfo(iServiceInformation.sVideoHeight)
			frame_rate = info.getInfo(iServiceInformation.sFrameRate)
			progressive = info.getInfo(iServiceInformation.sProgressive)
			print("yres", yres, "frame_rate", frame_rate, "progressive", progressive)
			if not progressive:
				frame_rate *= 2
			frame_rate = (frame_rate+500)//1000
			return "%d%s%d" % (yres, 'p' if progressive else 'i', frame_rate)
		elif self.type == self.VIDEO_TYPE:
			vtype = info.getInfo(iServiceInformation.sVideoType)
			return { CT_MPEG2 : "MPEG2", CT_H264 : "H.264", CT_MPEG1 : "MPEG1", CT_MPEG4_PART2 : "MPEG4", 
				  CT_VC1 : "VC1", CT_VC1_SIMPLE_MAIN : "WMV3", CT_H265 : "HEVC", CT_DIVX311 : "DIVX3", 
				  CT_DIVX4 : "DIVX4", CT_SPARK : "SPARK", CT_VP6 : "VP6", CT_VP8 : "VP8", 
				  CT_VP9 : "VP9", CT_H263 : "H.263", CT_MJPEG : "MJPEG", CT_REAL : "RV", 
				  CT_AVS : "AVS", CT_UNKNOWN : "UNK" }[vtype]
		return ""

	text = property(getText)

	@cached
	def getValue(self):
		service = self.source.service
		info = service and service.info()
		if not info:
			return -1

		if self.type == self.XRES:
			return info.getInfo(iServiceInformation.sVideoWidth)
		elif self.type == self.YRES:
			return info.getInfo(iServiceInformation.sVideoHeight)
		elif self.type == self.FRAMERATE:
			return info.getInfo(iServiceInformation.sFrameRate)
		elif self.type == self.IS_WIDESCREEN:
			return info.getInfo(iServiceInformation.sAspect)
		elif self.type == self.VIDEO_PARAMS:
			return -1 if info.getInfo(iServiceInformation.sVideoHeight) < 0 \
				or info.getInfo(iServiceInformation.sFrameRate) < 0 \
				or info.getInfo(iServiceInformation.sProgressive) < 0 \
				else -2
		return -1

	value = property(getValue)

	def changed(self, what):
		if what[0] != self.CHANGED_SPECIFIC or what[1] in self.interesting_events:
			Converter.changed(self, what)
		elif self.need_wa:
			if self.getValue() != -1:
				Converter.changed(self, (self.CHANGED_SPECIFIC, iPlayableService.evVideoSizeChanged))
				self.need_wa = False
