import xbmc
import xbmcaddon
import xbmcgui

import codecs
import io
import json
import os
import shutil
import string
import sys
import time
import unicodedata

import six

from xml.dom import minidom
from xml.etree import ElementTree

_addon = xbmcaddon.Addon()
_addon_id = _addon.getAddonInfo('id')
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_root = xbmc.translatePath(_addon.getAddonInfo('path'))
_art_path = os.path.join(_addon_root, 'resources', 'media')
if xbmc.getCondVisibility('System.HasAddon(script.skinshortcuts)'):
    _shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))
else:
    shortcuts_path = ''

windows = {'programs': ['program', 'script'],
            'addonbrowser': ['addon', 'addons'],
            'music': ['audio', 'music'],
            'pictures': ['image', 'picture'],
            'videos': ['video', 'videos']}
            
info_types = ['artist', 'albumartist', 'genre', 'year', 'rating',
              'album', 'track', 'duration', 'comment', 'lyrics',
              'musicbrainztrackid', 'plot', 'art', 'mpaa', 'cast',
              'musicbrainzartistid', 'set', 'showlink', 'top250', 'votes',
              'musicbrainzalbumid', 'disc', 'tag', 'genreid', 'season',
              'musicbrainzalbumartistid', 'size', 'theme', 'mood', 'style',
              'playcount', 'director', 'trailer', 'tagline', 'thumbnail',
              'plotoutline', 'originaltitle', 'lastplayed', 'writer', 'studio',
              'country', 'imdbnumber', 'premiered', 'productioncode', 'runtime',
              'firstaired', 'episode', 'showtitle', 'artistid', 'albumid',
              'tvshowid', 'setid', 'watchedepisodes', 'displayartist',
              'albumartistid', 'description', 'albumlabel', 'sorttitle',
              'dateadded', 'lastmodified', 'specialsortseason', 'mimetype', 
              'episodeguide', 'specialsortepisode']
              
info_list_types = ['artist', 'cast']
              
art_types = ['banner', 'clearart', 'clearlogo', 'fanart', 'icon', 'landscape',
             'poster', 'thumb']



def log(msg, level=xbmc.LOGDEBUG):
    msg = '{}: {}'.format(_addon_id, msg)
    xbmc.log(msg, level)


def ensure_addon_data():
    for path in [_addon_path, shortcuts_path]:
        if path:
            if not os.path.exists(path):
                os.makedirs(path)
                
                
def wipe(folder=_addon_path):
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', get_string(32065))
    
    if choice:
        shutil.rmtree(folder)


def set_skin_string(string, value):
    xbmc.executebuiltin('Skin.SetString({},{})'.format(string, value))
    
    
def get_skin_string(string):
    return xbmc.getInfoLabel('Skin.String({})'.format(string))
    
    
def get_art(filename):
    return {i: os.path.join(_art_path, i, filename) for i in art_types}
    
    
def get_active_window():
    if xbmc.getCondVisibility('Window.IsMedia()'):
        return 'media'
    elif xbmc.getCondVisibility('Window.IsActive(home)'):
        return 'home'
        
        
def update_container(reload=False, _type=''):
    if _type == 'shortcut':
        xbmc.executebuiltin('UpdateLibrary(video,AutoWidget)')
    if reload:
        xbmc.executebuiltin('ReloadSkin()')
        
    xbmc.executebuiltin('Container.Refresh()')

        
def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='\t')
    
   

def get_valid_filename(filename):
    whitelist = '-_.() {}{}'.format(string.ascii_letters, string.digits)
    char_limit = 255
    
    filename = filename.replace(' ','_')
    cleaned_filename = unicodedata.normalize('NFKD',
                                             filename).encode('ASCII',
                                                              'ignore').decode()
    
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
              
    return cleaned_filename[:char_limit]    
    
    
def get_unique_id(key):
    return '{}-{}'.format(get_valid_filename(six.ensure_text(key)),
                          time.time()).lower()
    
    
def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.items()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, six.text_type):
        return six.ensure_text(input)
        
    return input


def remove_file(file):
    try:
        os.remove(file)
    except Exception as e:
        log('Could not remove {}: {}'.format(file, e), level=xbmc.LOGERROR)


def read_file(file):
    content = None
    if os.path.exists(file):
        with io.open(file, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
            except Exception as e:
                log('Could not read from {}: {}'.format(file, e),
                    level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)
        
    return content
                      

def write_file(file, content):
    with open(file, 'w') as f:
        try:
            f.write(content)
            return True
        except Exception as e:
            log('Could not write to {}: {}'.format(file, e),
                level=xbmc.LOGERROR)
                
    return False
    
    
def read_json(file):
    data = None
    if os.path.exists(file):
        with codecs.open(file, 'r', encoding='utf-8') as f:
            try:
                content = six.ensure_text(f.read())
                data = json.loads(content)
            except Exception as e:
                log('Could not read JSON from {}: {}'.format(file, e),
                    level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)
        
    return convert(data)
    
    
def write_json(file, content):
    with codecs.open(file, 'w', encoding='utf-8') as f:
        try:
            json.dump(content, f, indent=4)
        except Exception as e:
            log('Could not write to {}: {}'.format(file, e),
                level=xbmc.LOGERROR)


def read_xml(file):
    xml = None
    if os.path.exists(file):
        try:
            xml = ElementTree.parse(file).getroot()
        except Exception as e:
            log('Could not read XML from {}: {}'.format(file, e),
                level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)
        
    return xml
    
    
def write_xml(file, content):
    prettify(content)
    tree = ElementTree.ElementTree(content)
    
    try:
        tree.write(file)
    except:
        log('Could not write to {}: {}'.format(file, e),
                  level=xbmc.LOGERROR)
                  
                  
def get_setting(setting):
    return _addon.getSetting(setting)

                  
def get_setting_bool(setting):
    try:
        return _addon.getSettingBool(setting)
    except:
        return bool(_addon.getSetting(setting))
        
        
def get_setting_int(setting):
    try:
        return _addon.getSettingInt(setting)
    except:
        return int(_addon.getSetting(setting))
        
        
def get_setting_float(setting):
    try:
        return _addon.getSettingNumber(setting)
    except:
        return float(_addon.getSetting(setting))
        
        
def get_string(_id):
    return six.text_type(_addon.getLocalizedString(_id))
