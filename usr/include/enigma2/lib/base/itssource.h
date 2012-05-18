#ifndef __lib_base_idatasource_h
#define __lib_base_idatasource_h

#include <lib/base/object.h>

class iTsSource: public iObject
{
public:
	 /* NOTE: should only be used to get current position or filelength */
	virtual uint64_t lseek(int64_t offset, int whence) = 0;
	
	/* NOTE: you must be able to handle short reads! */
	virtual ssize_t read(uint64_t offset, void *buf, size_t count)=0; /* NOTE: this is what you in normal case have to use!! */

	virtual uint64_t length() const = 0;
	virtual bool valid() const = 0;
};

#endif
