#ifndef __lib_system_init_num_
#define __lib_system_init_num_

namespace eAutoInitNumbers
{
	enum { increment=5 };
	enum
	{
		configuration=0,
		lowlevel=configuration+increment,
		network=lowlevel,
		graphic=lowlevel+increment,
		skin=graphic+increment,
		actions=skin+increment,
		rc=actions+increment,
		guiobject=rc+increment,
		dvb=guiobject+increment,
		service=dvb+increment,
		osd=service+increment,
		wizard=osd+increment,
		main=osd+increment*5,
	};
};

#endif
