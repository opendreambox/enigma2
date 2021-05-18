#ifndef __lib_parser_stream_streamprocessor_h
#define __lib_parser_stream_streamprocessor_h

#include <lib/base/ebase.h>
#include <lib/service/iservice.h>
#include <lib/parser/stream/istream.h>
#include <vector>
#include <string>
#include <memory>

class StreamManager;
class eStreamProcessor;

class eStreamProcessorFactory
{
	static std::vector<eStreamProcessorFactory*> s_factories;

public:
	eStreamProcessorFactory(const std::string &name, int priority = 0);
	virtual ~eStreamProcessorFactory();

	const std::string &getName() const;
	int getPriority() const;

	virtual bool canProcess(const std::vector<StreamInfo> &streamInfos) const = 0;
	virtual std::shared_ptr<eStreamProcessor> create(StreamManager &streamManager) const = 0;

	static void registerFactory(eStreamProcessorFactory* factory);
	static const std::vector<eStreamProcessorFactory*> &getFactories();
	static eSignal1<void, eStreamProcessorFactory*> factoryAdded;
private:
	const std::string m_name;
	int m_prio;
};

class eStreamProcessor
{
	SWIG_AUTODOC
public:
	virtual ~eStreamProcessor();

	const eServiceReference &getServiceReference() const;
	bool valid() const;

	virtual void start() = 0;
	virtual void stop() = 0;
	virtual bool pause() = 0;
	virtual bool resume() = 0;
	virtual void seekDone(int status) = 0;
	virtual void flush() = 0;

	virtual void parsed() = 0;
	virtual void ready() = 0;

	const std::vector<StreamInfo> &getStreams() const;
	bool selectVideoStream(int index, const StreamRestrictions &restrictions = StreamRestrictions());
	bool selectAudioStream(int index, const StreamRestrictions &restrictions = StreamRestrictions());
	void deleteStream(int index);

	int getActiveVideoIndex() const;
	int getActiveAudioIndex() const;
	virtual int getActiveAudioCodec() const = 0;

	virtual bool getWidth(int &width) const;
	virtual bool getHeight(int &height) const;
	virtual bool getAspect(int &aspect) const;
	virtual bool getFramerate(int &framerate) const;
	virtual bool getProgressive(int &progressive) const;
	virtual bool isEOS() const;

	bool getVideoFrames(std::vector<RawData> &frames);
	bool getAudioPackets(std::vector<RawData> &packets);

	eSignal1<void, bool> streamStarted; // emitted when buffer is ready after first start or seek

	eSignal3<void, int, int, int> formatChanged;
	eSignal1<void, int> framerateChanged;
	eSignal1<void, int> progressiveChanged;
	eSignal0<void> videoPtsValid;

	eSignal0<void> lastVideoConsumed;
	eSignal0<void> lastAudioConsumed;

	eSignal0<void> audioCodecChanged;

protected:
	eStreamProcessor(StreamManager &streamManager);

private:
	StreamManager &m_streamManager;
	std::shared_ptr<iStream> m_stream;
	bool m_audioNeedsSync;
};

#endif
