#ifndef __lib_parser_stream_stream_h
#define __lib_parser_stream_stream_h

#include <string>
#include <vector>
#include <stdint.h>
#include <mutex>
#include <lib/base/ebase.h>
#include <lib/parser/container/sample.h>

struct VideoCodecInfo
{
	std::string type; // h264, etc.
	int width;
	int height;
	int bitrate;
	double framerate;
	double aspect;
	std::vector<uint8_t> extraData;

	std::vector<std::map<std::string, std::string>> protections;
};

struct AudioCodecInfo
{
	std::string type;
	int samplerate;
	int channels;
	int misc;
	int bitrate;
	int block_align;
	std::vector<uint8_t> extraData;
	std::string raw_format;
	int mpeg_version;

	std::vector<std::map<std::string, std::string>> protections;
};

struct SubtitleInfo
{
	std::string codecs;
	std::string role;
	std::string url;
};

enum ContentType
{
	UNKNOWN = -1,
	VIDEO,
	AUDIO,
	TEXT,
	MIXED = 100
};

struct StreamInfo
{
	StreamInfo() :
		type(ContentType::UNKNOWN),
		activeIndex(0)
	{}

	ContentType type;
	std::string mimeType;

	std::string language;
	int activeIndex;

	std::vector<VideoCodecInfo> videoCodecInfo;
	std::vector<AudioCodecInfo> audioCodecInfo;
	std::vector<SubtitleInfo> subtitleInfo;
};

struct StreamRestrictions
{
	unsigned maxWidth;
	unsigned maxHeight;
	unsigned maxBandwidth;
};

class iStream
{
public:
	iStream() :	m_valid(false) {}
	virtual ~iStream() {}

	virtual void init() = 0;

	virtual const std::vector<StreamInfo> &getStreams() const = 0;
	virtual void deleteStream(int index) = 0;
	virtual bool selectStream(int index, const StreamRestrictions &restrictions = StreamRestrictions()) = 0;

	virtual bool isLive() const = 0;
	virtual bool isReady() const = 0;
	virtual void rebuffer() = 0;
	virtual int64_t getDuration() const = 0;
	virtual bool seek(int64_t pts, int index = -1) = 0;
	virtual bool getVideoFrames(std::vector<RawData> &rawData) = 0;
	virtual bool getAudioPackets(std::vector<RawData> &rawData) = 0;
	bool valid() const { std::lock_guard<std::mutex> lk(m_mtx); return m_valid; }

	eSignal0<void> initialized; // emit when meta data is ready
	eSignal0<void> parsed; // emit when stream init data was parsed (MP4: init segment, TS: PAT/PMT)
	eSignal0<void> ready; // emit when buffer is okay for the first time
	eSignal1<void, int> seekDone;
	eSignal0<void> videoEOS;
	eSignal0<void> audioEOS;

protected:
	mutable std::mutex m_mtx;
	bool m_valid;
};

#endif
