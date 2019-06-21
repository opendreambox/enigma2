#ifndef __LIB_DRIVER_ALSA_H_
#define __LIB_DRIVER_ALSA_H_

#include <lib/base/ebase.h>

#define PCM_FRAMES 64
#define PCM_CHUNK_SIZE (8 * 1024)

class eAlsaOutput
{
	E_DECLARE_PRIVATE(eAlsaOutput);
	E_DISABLE_COPY(eAlsaOutput);

public:
	enum { HDMI, SPDIF, BTPCM };

	static eAlsaOutput *instance[3];
	static eAlsaOutput *getInstance(int type = HDMI);

	eAlsaOutput(int type);
	~eAlsaOutput();

	bool running() const;
	int close();
	int pause(int state);
	int stop();
	int start(unsigned int rate, unsigned int channels, unsigned int bits, const sigc::slot<int64_t> &get_stc, const sigc::slot<void> &buffer_consumed);
	int pushData(uint8_t *data, int size, int64_t pts);
	uint64_t fifoFillClockTicks() const;
	int fifoFill() const;
	int fifoSize() const;
	void flushFifo();
	int64_t getPTS();
};

#endif // __LIB_DRIVER_ALSA_H_
