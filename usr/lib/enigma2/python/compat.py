# please do not add from __future__ import division here 
# to not break the following workaround

# this is a temporary hack to fix problems 
# with embedded code in external plugins / skins 
def skin_applet_compile(source, filename, flags):
	return compile(source, filename, flags)
