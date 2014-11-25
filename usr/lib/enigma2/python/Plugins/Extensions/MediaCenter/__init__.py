# -*- coding: UTF-8 -*-

from Components.config import config, ConfigSubsection, ConfigInteger

#some minor magic, please don't remove those
try: #systemplugins-upnp may not be installed
	from MediaBrowserUPnP import MediaBrowserUPnP
except:
	print "[MediaCenter] UPnP/DLNA not installed, though not available"
from MediaBrowserFile import MediaBrowserFile
from MediaBrowserDB import MediaBrowserDB
from MediaBrowserSearch import MediaBrowserSearch

#init the config
config.plugins.mediacenter = ConfigSubsection()
config.plugins.mediacenter.video = ConfigSubsection()
config.plugins.mediacenter.video.last_playlist_id = ConfigInteger(-1, limits=[-1,9999999999])
config.plugins.mediacenter.audio = ConfigSubsection()
config.plugins.mediacenter.audio.last_playlist_id = ConfigInteger(-1, limits=[-1,9999999999])


