#ifndef __dvb_demux_h
#define __dvb_demux_h

#include <lib/dvb/idvb.h>
#include <lib/dvb/idemux.h>

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

	friend class eDVBSectionReader;
	friend class eDVBPESReader;
	friend class eDVBAudio;
	friend class eDVBVideo;
	friend class eDVBPCR;
	friend class eDVBTText;
	friend class eDVBTSRecorder;
	friend class eDVBCAService;
	sigc::signal1<void, int> m_event;
	
	int openDemux(void);
};

class eDVBSectionReader: public iDVBSectionReader, public sigc::trackable
{
	DECLARE_REF(eDVBSectionReader);
	int fd;
	sigc::signal2<void, const __u8*, int> read;
	ePtr<eDVBDemux> demux;
	int active;
	int checkcrc;
	void data(int);
	ePtr<eSocketNotifier> notifier;
	Slot0<__u8*> m_buffer_func;
	bool m_have_external_buffer_func;
public:
	eDVBSectionReader(eDVBDemux *demux, eMainloop *context, RESULT &res);
	virtual ~eDVBSectionReader();
	RESULT setBufferSize(int size);
	RESULT start(const eDVBSectionFilterMask &mask);
	RESULT startWithExternalBufferFunc(const eDVBSectionFilterMask &mask, const Slot0<__u8*> &buffer_func);
	RESULT stop();
	RESULT connectRead(const sigc::slot2<void,const __u8*, int> &read, ePtr<eConnection> &conn);
};

class eDVBPESReader: public iDVBPESReader, public sigc::trackable
{
	DECLARE_REF(eDVBPESReader);
	int m_fd;
	sigc::signal2<void, const __u8*, int> m_read;
	ePtr<eDVBDemux> m_demux;
	int m_active;
	void data(int);
	ePtr<eSocketNotifier> m_notifier;
public:
	eDVBPESReader(eDVBDemux *demux, eMainloop *context, RESULT &res);
	virtual ~eDVBPESReader();
	RESULT setBufferSize(int size);
	RESULT start(int pid);
	RESULT stop();
	RESULT connectRead(const sigc::slot2<void,const __u8*, int> &read, ePtr<eConnection> &conn);
};

class eDVBRecordFileThread;

class eDVBTSRecorder: public iDVBTSRecorder, public sigc::trackable
{
	DECLARE_REF(eDVBTSRecorder);
public:
	eDVBTSRecorder(eDVBDemux *demux);
	~eDVBTSRecorder();

	RESULT setBufferSize(int size);
	RESULT start();
	RESULT addPID(int pid);
	RESULT removePID(int pid);
	
	RESULT setTimingPID(int pid, int type);
	
	RESULT setTargetFD(int fd);
	RESULT setTargetFilename(const char *filename);
	
	RESULT stop();

	RESULT getCurrentPCR(pts_t &pcr);

	RESULT connectEvent(const sigc::slot1<void,int> &event, ePtr<eConnection> &conn);
private:
	RESULT startPID(int pid);
	void stopPID(int pid);
	
	eDVBRecordFileThread *m_thread;
	void filepushEvent(int event);
	
	std::map<int,int> m_pids;
	sigc::signal1<void,int> m_event;
	
	ePtr<eDVBDemux> m_demux;
	
	int m_running, m_target_fd, m_source_fd;
	std::string m_target_filename;
};

#endif
