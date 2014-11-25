#ifndef __src_lib_base_buffer_h
#define __src_lib_base_buffer_h

#include <lib/base/smartptr.h>
#include <lib/base/object.h>

#include <asm/types.h>
#include <list>

#ifndef SWIG

/**
 * IO buffer.
 */
class eIOBuffer
{
	int allocationsize;
	struct eIOBufferData
	{
		__u8 *data;
		int len;
	};
	std::list<eIOBufferData> buffer;
	void removeblock();
	eIOBufferData &addblock();
	int ptr;
public:
	eIOBuffer(int allocationsize): allocationsize(allocationsize), ptr(0)
	{
	}
	~eIOBuffer();
	int size() const;
	int empty() const;
	void clear();
	int peek(void *dest, int len) const;
	void skip(int len);
	int read(void *dest, int len);
	void write(const void *source, int len);
	int fromfile(int fd, int len);
	int tofile(int fd, int len);

	int searchchr(char ch) const;
};

#endif

typedef enum { MALLOC, NEW } alloc_type_t;

SWIG_IGNORE(Buffer);
class Buffer: public iObject
{
	DECLARE_REF(Buffer);
	alloc_type_t m_type;
	unsigned char *m_data;
	size_t m_len;
public:
	Buffer(alloc_type_t type=NEW)
		:m_type(type), m_data(NULL), m_len(0)
	{}
	Buffer(unsigned char *data, size_t len, alloc_type_t type=NEW)
		:m_type(type), m_data(data), m_len(len)
	{}
	~Buffer()
	{
		if (m_data)
		{
			if (m_type == MALLOC)
				free(m_data);
			else
				delete [] m_data;
		}
	}
	const unsigned char *data() const { return m_data; }
	size_t size() const { return m_len; }
	void setBuffer(unsigned char *b) { m_data = b; }
	void setSize(size_t size) { m_len = size; }
};
SWIG_TEMPLATE_TYPEDEF(ePtr<Buffer>, BufferPtr);

#endif
