#ifndef __lib_parser_stream_streamprocessor_h
#define __lib_parser_stream_streamprocessor_h

#include <lib/base/ebase.h>
#include <lib/parser/stream/istream.h>
#include <vector>
#include <string>

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

	virtual void start() = 0;
	virtual void stop() = 0;
	virtual bool pause() = 0;
	virtual bool resume() = 0;
	virtual void seekDone(int status) = 0;

	virtual bool canProcess(std::vector<StreamInfo> &streamInfos) = 0;
	virtual void parsed() = 0;
	virtual void ready() = 0;

	std::vector<StreamInfo> &getStreams();
	bool selectVideoStream(int index, const StreamRestrictions &restrictions = StreamRestrictions());
	bool selectAudioStream(int index, const StreamRestrictions &restrictions = StreamRestrictions());
	void deleteStream(int index);

	int getActiveVideoIndex() const;
	int getActiveAudioIndex() const;

	bool getVideoFrames(std::vector<RawData> &frames);
	bool getAudioPackets(std::vector<RawData> &packets);

#ifndef SWIG
	void setStreamManager(StreamManager* streamManager);
#endif

	static const std::vector<eStreamProcessor*> &getProcessors();
	static void addProcessor(eStreamProcessor* processor);

	eSignal3<void, int, int, int> formatChanged;
	eSignal1<void, int> framerateChanged;
	eSignal1<void, int> progressiveChanged;

private:
	StreamManager *m_streamManager;
};

#endif
