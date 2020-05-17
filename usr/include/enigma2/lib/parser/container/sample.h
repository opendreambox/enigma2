#pragma once

#include <cstdint>
#include <functional>
#include <vector>

enum class StreamEncryptionType
{
	NONE,
	UNKNOWN
};

enum class StreamRawType
{
	UNKNOWN,
	VIDEO,
	AUDIO
};

enum StreamRawFlags
{
	DISCONTINUITY = 1
};

struct RawData
{
	RawData() :
		type(StreamRawType::UNKNOWN),
		pts(0),
		offset(0),
		encType(StreamEncryptionType::NONE),
		flags(0)
	{
	}

	StreamRawType type;
	std::vector<uint8_t> data;
	int64_t pts;
	uint64_t offset;
	StreamEncryptionType encType;

	int flags;

	// Crypto stuff (unused)
	std::vector<uint8_t> iv;
	uint16_t subsampleCount;
	std::vector<int> clearBytes;
	std::vector<int> cryptoBytes;
};
