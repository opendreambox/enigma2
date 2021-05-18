#ifndef __dvb_idemux_h
#define __dvb_idemux_h

#include <lib/dvb/idvb.h>

class iDVBSectionReader: public iObject
{
public:
	virtual RESULT setBufferSize(int size)=0;
	virtual RESULT start(const eDVBSectionFilterMask &mask)=0;
	virtual RESULT startWithExternalBufferFunc(const eDVBSectionFilterMask &mask, const Slot0<__u8*> &buffer_func)=0;
	virtual RESULT stop()=0;
	virtual RESULT connectRead(const sigc::slot2<void,const __u8*, int> &read, ePtr<eConnection> &conn)=0;
	virtual ~iDVBSectionReader() { };
};

class iDVBTSReader: public iObject
{
public:
	enum {
		typeOther=0,
		typeVideo0=1,
		typeVideo1=2,
		typeVideo2=3,
		typeAudio0=4,
		typeAudio1=5,
		typeAudio2=6,
	};
	virtual RESULT setBufferSize(int size)=0;
	virtual RESULT configure(int pid, int type) = 0;
	virtual RESULT start()=0;
	virtual RESULT start(int pid, int type)=0;
	virtual RESULT stop()=0;
	virtual RESULT addPID(int pid) = 0;
	virtual RESULT removePID(int pid) = 0;

	virtual bool paused()=0;
	virtual void pause()=0;
	virtual void resume()=0;

	virtual bool active()=0;
	virtual RESULT connectRead(const sigc::slot2<void,const __u8*, int> &read, ePtr<eConnection> &conn)=0;
	virtual ~iDVBTSReader() { };

	virtual void close() { }; // workaround to close a fd to interrupt a pending read for faster stop response... default a NOP
	virtual bool closePending() { return false;  }

	virtual ssize_t read(unsigned char *d, int bytes)=0; 	/* for blocking reads.. on create context must be NULL */
};

class iDVBPESReader: public iObject
{
public:
	virtual RESULT setBufferSize(int size)=0;
	virtual RESULT start(int pid)=0;
	virtual RESULT stop()=0;
	virtual RESULT connectRead(const sigc::slot2<void,const __u8*, int> &read, ePtr<eConnection> &conn)=0;
	virtual ~iDVBPESReader() { };
};

	/* records a given set of pids into a file descriptor. */
	/* the FD must not be modified between start() and stop() ! */
class iDVBTSRecorder: public iObject
{
public:
	virtual RESULT setBufferSize(int size) = 0;
	virtual RESULT start() = 0;
	virtual RESULT addPID(int pid) = 0;
	virtual RESULT removePID(int pid) = 0;
	
	virtual RESULT setTimingPID(int pid, int type) = 0;
	
	virtual RESULT setTargetFD(int fd) = 0;
		/* for saving additional meta data. */
	virtual RESULT setTargetFilename(const char *filename) = 0;
	virtual RESULT setAccessPoints(bool on) = 0;
	
	virtual RESULT stop() = 0;

	virtual RESULT getCurrentPCR(pts_t &pcr) = 0;
	
	enum {
		eventWriteError,
				/* a write error has occured. data won't get lost if fd is writable after return. */
				/* you MUST respond with either stop() or fixing the problems, else you get the error */
				/* again. */
		eventReachedBoundary,
				/* the programmed boundary was reached. you might set a new target fd. you can close the */
				/* old one. */
	};
	virtual RESULT connectEvent(const sigc::slot1<void,int> &event, ePtr<eConnection> &conn)=0;
};

class iDVBTSWriter: public iObject
{
public:
	virtual ssize_t processData(const unsigned char *data, size_t bytes) = 0;
	virtual void flush() = 0;
	virtual int waitEOF() = 0;
};

#endif
