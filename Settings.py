#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__author__ = "iEpic"
__email__ = "epicunknown@gmail.com"
"""

import os
import json


class Settings:

    def __init__(self):
        self.loaded_settings = {}
        # Does settings.json file exist?
        if os.path.exists('settings.json'):
            # Load up the settings
            with open('settings.json') as file:
                self.loaded_settings = json.load(file)
                print('Settings Loaded.')
        else:
            # Lets create a new settings file
            self.loaded_settings['includeShowDesc'] = True
            self.loaded_settings['saveFormat'] = '{show}-S{season}E{episode}-{desc}'
            self.loaded_settings['episodePadding'] = 2
            self.loaded_settings['seasonPadding'] = 2
            self.loaded_settings['defaultOutputLocation'] = False
            self.loaded_settings['saveDownloadLocation'] = True
            self.loaded_settings['useKnownDownloadLocation'] = True
            self.loaded_settings['checkIfFileIsAlreadyDownloaded'] = True
            self.loaded_settings['downloadsDatabaseLocation'] = ".{os_path}{file_name}".format(os_path=os.sep, file_name='database.p')
            self.loaded_settings['allowToResumeDownloads'] = True
            self.loaded_settings['checkForUpdates'] = True
            
            file = open('settings.json', 'w')
            file.write(json.dumps(self.loaded_settings, indent=4, sort_keys=True))
            file.close()
            print('Settings have been created!')

    def get_setting(self, setting_name):
        if setting_name in self.loaded_settings:
            return self.loaded_settings[setting_name]
