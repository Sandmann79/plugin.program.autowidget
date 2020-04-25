import xbmcgui
import xbmcplugin

import string
import sys

from resources.lib.common import utils

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import encode

sync = utils.get_art('sync.png')

    
def add_separator(title='', char='-'):
    _window = utils.get_active_window()
    if _window != 'media':
        return

    if title:
        if isinstance(title, int):
            title = utils.get_string(title)
            
        split = (len(title) + 2) / 2
        edge = char * int(40 - split)
        add_menu_item(title='{0} {1} {0}'.format(edge, string.capwords(title)),
                      art=sync)
    else:
        add_menu_item(title=char * 80, art=sync)

    
def add_menu_item(title, params=None, info=None, cm=None, art=None,
                  is_folder=False):
    _plugin, _handle = sys.argv[:1]
    _params = sys.argv[2][1:]

    if params is not None:
        _plugin += '?{}'.format(urlencode(params))

    if isinstance(title, int):
        title = utils.get_string(title)
    
    def_info = {}
    if info:
        def_info.update(info)
        for key in def_info:
            if any(key == i for i in utils.info_list_types):
                i = def_info[key]
                if not i:
                    def_info[key] = []
                elif not isinstance(i, list):
                    def_info[key] = [def_info[key]]
    
    def_art = {}
    if art:
        def_art.update(art)
    
    def_cm = []    
    if cm:
        def_cm.extend(cm)
        
    item = xbmcgui.ListItem(title)
    item.setInfo('video', def_info)
    item.setArt(def_art)
    item.addContextMenuItems(def_cm)
    
    xbmcplugin.addDirectoryItem(handle=_handle, url=_plugin, listitem=item,
                                isFolder=is_folder)
