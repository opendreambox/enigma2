#ifndef __lib_parser_stream_stream_h
#define __lib_parser_stream_stream_h

#include <string>
#include <vector>
#include <stdint.h>
#include <lib/base/ebase.h>


enum class StreamEncryptionType
{
	NONE,
	UNKNOWN,
	WIDEVINE
};

enum class StreamRawType
{
	UNKNOWN,
	VIDEO,
	AUDIO
};

struct RawData
{
	RawData() : type(StreamRawType::UNKNOWN), pts(0), offset(0), encType(StreamEncryptionType::NONE) {}
	StreamRawType type;
	std::vector<uint8_t> data;
	int64_t pts;
	uint64_t offset;
	StreamEncryptionType encType;

	// Crypto stuff (unused)
	std::vector<uint8_t> iv;
	uint16_t subsampleCount;
	std::vector<int> clearBytes;
	std::vector<int> cryptoBytes;

};

struct VideoCodecInfo
{
	std::string type; // h264, etc.
	int width;
	int height;
	int bitrate;
	double framerate;
	double aspect;
	std::vector<uint8_t> extraData;
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
};

struct StreamInfo
{
	int type; // video / audio
	std::string language;
	int activeIndex;

	std::vector<std::map<std::string, std::string>> protections;

	std::vector<VideoCodecInfo> videoCodecInfo;
	std::vector<AudioCodecInfo> audioCodecInfo;
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

	virtual std::vector<StreamInfo> &getStreams() = 0;
	virtual void deleteStream(int index) = 0;
	virtual bool selectStream(int index, const StreamRestrictions &restrictions = StreamRestrictions()) = 0;

	virtual bool isLive() = 0;
	virtual bool isReady() = 0;
	virtual int64_t getDuration() = 0;
	virtual bool seek(int64_t pts, int index = -1) = 0;
	virtual bool getVideoFrames(std::vector<RawData> &rawData) = 0;
	virtual bool getAudioPackets(std::vector<RawData> &rawData) = 0;
	bool valid() const { return m_valid; }

	eSignal0<void> initialized;
	eSignal0<void> parsed;
	eSignal0<void> ready;
	eSignal0<void> seekDone;

protected:
	bool m_valid;
};

#endif
