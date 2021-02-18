#ifndef __lib_parser_stream_streamprocessor_h
#define __lib_parser_stream_streamprocessor_h

#include <lib/base/ebase.h>
#include <lib/parser/stream/istream.h>
#include <vector>
#include <string>
#include <memory>

class StreamManager;

class eStreamProcessor
{
	SWIG_AUTODOC
	static std::vector<eStreamProcessor*> s_processors;
	std::string m_name;

public:
	eStreamProcessor(const std::string &name);
	virtual ~eStreamProcessor();

	const std::string &getName() const;
	bool valid() const;

	virtual void start() = 0;
	virtual void stop() = 0;
	virtual bool pause() = 0;
	virtual bool resume() = 0;
	virtual void seekDone(int status) = 0;
	virtual void flush() = 0;

	virtual bool canProcess(std::vector<StreamInfo> &streamInfos) = 0;
	virtual void parsed() = 0;
	virtual void ready() = 0;

	std::vector<StreamInfo> &getStreams();
	bool selectVideoStream(int index, const StreamRestrictions &restrictions = StreamRestrictions());
	bool selectAudioStream(int index, const StreamRestrictions &restrictions = StreamRestrictions());
	void deleteStream(int index);

	int getActiveVideoIndex() const;
	int getActiveAudioIndex() const;
	virtual int getActiveAudioCodec() = 0;

	virtual bool getWidth(int &width) const;
	virtual bool getHeight(int &height) const;
	virtual bool getAspect(int &aspect) const;
	virtual bool getFramerate(int &framerate) const;
	virtual bool getProgressive(int &progressive) const;
	virtual bool isEOS() const;

	bool getVideoFrames(std::vector<RawData> &frames);
	bool getAudioPackets(std::vector<RawData> &packets);

#ifndef SWIG
	void setStreamManager(StreamManager* streamManager);
#endif

	static const std::vector<eStreamProcessor*> &getProcessors();
	static void addProcessor(eStreamProcessor* processor);
	static eSignal1<void, eStreamProcessor*> processorAdded;

	eSignal1<void, bool> streamStarted; // emitted when buffer is ready after first start or seek

	eSignal3<void, int, int, int> formatChanged;
	eSignal1<void, int> framerateChanged;
	eSignal1<void, int> progressiveChanged;
	eSignal0<void> videoPtsValid;

	eSignal0<void> lastVideoConsumed;
	eSignal0<void> lastAudioConsumed;

	eSignal0<void> audioCodecChanged;

private:
	StreamManager *m_streamManager;
	std::shared_ptr<iStream> m_stream;
	bool m_audioNeedsSync;
};

#endif
