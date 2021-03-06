import xbmc
import xbmcgui

import os
import random
import time

from resources.lib import convert
from resources.lib import manage
from resources.lib.common import utils

skin_string_pattern = 'autowidget-{}-{}'
_properties = ['context.autowidget']

class RefreshService(xbmc.Monitor):

    def __init__(self):
        utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)
        self.player = xbmc.Player()
        utils.ensure_addon_data()
        self._update_properties()
        self._update_widgets()

    def onSettingsChanged(self):
        self._update_properties()

    def _reload_settings(self):
        self.refresh_enabled = utils.get_setting_int('service.refresh_enabled')
        self.refresh_duration = utils.get_setting_float('service.refresh_duration')
        self.refresh_notification = utils.get_setting_int('service.refresh_notification')

    def _update_properties(self, window=10000):

        for property in _properties:
            setting = utils.get_setting(property)
            utils.log('{}: {}'.format(property, setting))
            if setting is not None:
                xbmcgui.Window(window).setProperty(property, setting)
                utils.log('Property {0} set'.format(property))
            else:
                xbmcgui.Window(window).clearProperty(property)
                utils.log('Property {0} cleared'.format(property))

        self._reload_settings()
        
    def _refresh(self):
        if self.refresh_enabled in [0, 1] and manage.find_defined_widgets():
            notification = False
            if self.refresh_enabled == 1:
                if self.player.isPlayingVideo():
                    utils.log('+++++ PLAYBACK DETECTED, SKIPPING AUTOWIDGET REFRESH +++++',
                              level=xbmc.LOGNOTICE)
                    return
            else:
                if self.refresh_notification == 0:
                    notification = True
                elif self.refresh_notification == 1:
                    if not self.player.isPlayingVideo():
                        notification = True
            
            utils.log('+++++ REFRESHING AUTOWIDGETS +++++', level=xbmc.LOGNOTICE)
            refresh_paths(notify=notification)
        else:
            utils.log('+++++ AUTOWIDGET REFRESHING NOT ENABLED +++++',
                      level=xbmc.LOGNOTICE)

    def _update_widgets(self):
        self._refresh()
        
        while not self.abortRequested():
            if self.waitForAbort(60 * 15):
                break

            if not self._refresh():
                continue



def _update_strings(_id, path_def, setting=None, label_setting=None):
    if not path_def:
        return
    
    label = path_def['label']
    action = path_def['path']
    
    try:
        label = label.encode('utf-8')
    except:
        pass
    
    if setting:
        if label_setting:
            utils.log('Setting {} to {}'.format(label_setting, label))
            utils.set_skin_string(label_setting, label)
        
        utils.log('Setting {} to {}'.format(setting, action))
        utils.set_skin_string(setting, action)
    else:
        target = path_def['window']
        label_string = skin_string_pattern.format(_id, 'label')
        action_string = skin_string_pattern.format(_id, 'action')
        target_string = skin_string_pattern.format(_id, 'target')

        utils.log('Setting {} to {}'.format(label_string, label))
        utils.log('Setting {} to {}'.format(action_string, action))
        utils.log('Setting {} to {}'.format(target_string, target))
        utils.set_skin_string(label_string, label)
        utils.set_skin_string(action_string, action)
        utils.set_skin_string(target_string, target)


def refresh(widget_id, widget_def=None, paths=None, force=False):
    if not widget_def:
        widget_def = manage.get_widget_by_id(widget_id)
    
    current_time = time.time()
    updated_at = widget_def.get('updated', 0)
    
    default_refresh = utils.get_setting_float('service.refresh_duration')
    refresh_duration = float(widget_def.get('refresh', default_refresh))
            
    if updated_at <= current_time - (3600 * refresh_duration) or force:
        path_def = {}
        
        _id = widget_def['id']
        group_id = widget_def['group']
        action = widget_def.get('action')
        setting = widget_def.get('path_setting')
        label_setting = widget_def.get('label_setting')
        current = int(widget_def.get('current', -1))
        
        if not paths:
            paths = manage.find_defined_paths(group_id)
            random.shuffle(paths)
        
        if action:
            if len(paths) > 0:
                next = 0
                if action == 'next':
                    next = (current + 1) % len(paths)
                elif action == 'random':
                    next = random.randrange(len(paths))
                    
                widget_def['current'] = next
                path_def = paths[next]
                paths.remove(paths[next])            
                
                widget_def['path'] = path_def.get('id')
                if widget_def['path']:
                    widget_def['updated'] = 0 if force else current_time
                        
                    convert.save_path_details(widget_def, _id)
                    _update_strings(_id, path_def, setting, label_setting)
                    
                    utils.update_container()
    
    return paths


def refresh_paths(notify=False, force=False):
    converted = []
    current_time = time.time()
    
    if force:
        converted = convert.convert_widgets(notify)

    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', utils.get_string(32033))
    
    for group_def in manage.find_defined_groups():
        paths = []
        
        widgets = manage.find_defined_widgets(group_def['id'])
        for widget_def in widgets:
            paths = refresh(widget_def['id'], widget_def=widget_def, paths=paths, force=force)

    utils.update_container(reload=len(converted) > 0 and utils.shortcuts_path)
