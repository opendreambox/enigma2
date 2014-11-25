from Components.config import config, ConfigYesNo, ConfigEnableDisable, ConfigText, ConfigInteger, ConfigSubsection
from Tools.HardwareInfo import HardwareInfo

config.plugins.mediaserver = ConfigSubsection()
config.plugins.mediaserver.enabled = ConfigEnableDisable(default=True)
config.plugins.mediaserver.share_audio = ConfigYesNo(default=True)
config.plugins.mediaserver.share_video = ConfigYesNo(default=True)
config.plugins.mediaserver.share_live = ConfigYesNo(default=True)
config.plugins.mediaserver.name = ConfigText(default="%s Mediaserver" %(HardwareInfo().get_device_name()), fixed_size = False)
config.plugins.mediaserver.uuid = ConfigText(default="", fixed_size = False)
config.plugins.mediaserver.album_art_names = ConfigText("Cover.jpg/cover.jpg/AlbumArtSmall.jpg/albumartsmall.jpg/AlbumArt.jpg/albumart.jpg/Album.jpg/album.jpg/Folder.jpg/folder.jpg/Thumb.jpg/thumb.jpg", fixed_size = False)
