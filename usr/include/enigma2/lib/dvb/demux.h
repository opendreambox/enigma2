#ifndef __dvb_demux_h
#define __dvb_demux_h

#include <lib/dvb/idvb.h>
#include <lib/dvb/idemux.h>

class eDVBSectionReader;
class eDVBPESReader;
class eDVBTSReader;
class eDVBTSRecorder;

class eDVBDemux: public iDVBDemux
{
	DECLARE_REF(eDVBDemux);
public:
	enum {
		evtFlush
	};
	eDVBDemux(int adapter, int demux);
	virtual ~eDVBDemux();
	
	RESULT setSourceFrontend(int fenum);
	int getSource() const { return source; }
	RESULT setSourcePVR(const std::string &pvr_source);
	std::string getSourcePVR() const { return pvr_source; }

	RESULT createSectionReader(eMainloop *context, ePtr<iDVBSectionReader> &reader);
	RESULT createPESReader(eMainloop *context, ePtr<iDVBPESReader> &reader);
	RESULT createTSReader(eMainloop *context, ePtr<iDVBTSReader> &reader);
	RESULT createTSWriter(ePtr<iDVBTSWriter> &writer);
	RESULT createTSRecorder(ePtr<iDVBTSRecorder> &recorder);
	RESULT getMPEGDecoder(ePtr<iTSMPEGDecoder> &reader, int decoder_id);
	RESULT getSTC(pts_t &pts, int num);
	RESULT getCADemuxID(uint8_t &id) { id = demux; return 0; }
	RESULT flush();
	RESULT connectEvent(const sigc::slot1<void,int> &event, ePtr<eConnection> &conn);
	int openDVR(int flags);

	int getRefCount() { return ref; }
private:
	int adapter, demux, source;
	std::string pvr_source;
	int m_pcr_fd;

	friend class eDVBSectionReader;
	friend class eDVBPESReader;
	friend class eDVBTSReader;
	friend class eDVBAudio;
	friend class eDVBVideo;
	friend class eDVBPCR;
	friend class eDVBTText;
	friend class eDVBTSRecorder;
	friend class eDVBCAService;
	sigc::signal1<void, int> m_event;
	
	int openDemux(void);
};

#endif
