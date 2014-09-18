from datetime import datetime
import itertools
import os
from os.path import basename, exists, expanduser, join, normcase
from os.path import normpath, realpath, sep
import re
import shutil

from libsyntyche.common import read_json, read_file, write_json, write_file
from libsyntyche.common import local_path, make_sure_config_exists
from pluginlib import GUIPlugin

class UserPlugin(GUIPlugin):
    def __init__(self, objects, get_path):
        super().__init__(objects, get_path)
        self.textarea = objects['textarea']
        self.textarea.file_saved.connect(self.on_save)
        self.configpath = objects['settingsmanager'].get_config_directory()
        self.local_path = get_path()
        self.commands = {'l': (self.start_logging, 'Start logging this file (y for offset, n for no offset, omit argument for only info)')}

    def read_config(self):
        configfile = join(self.configpath, 'kalpana-logger.conf')
        defaultconfigfile = join(self.local_path, 'defaultconfig.json')
        make_sure_config_exists(configfile, defaultconfigfile)
        self.settings = read_json(configfile)

    def start_logging(self, arg):
        arg = arg.lower().strip()
        filepath = self.textarea.file_path
        if not filepath:
            self.error('Can\'t log an unnamed file! Save and try again (without offset)')
            return
        # Paths
        logdir, indexpath, relative_filepath = self.get_logpaths()
        index = get_index(indexpath)
        if not arg:
            if relative_filepath in index:
                self.print_('File is being logged.')
            else:
                self.print_('File is not being logged.')
            return
        if arg not in ('y','n'):
            self.error('Argument should be y/n! (use offset/no offset)')
            return
        if relative_filepath in index:
            self.error('File already logged!')
            return
        # Offsets
        if arg == 'y':
            offset = len(re.findall(r'\S+', read_file(self.textarea.file_path)))
        else:
            offset = 0
        # Init
        logfname = generate_logfilename(logdir, relative_filepath)
        index[relative_filepath] = logfname
        write_file(join(logdir, logfname), str(offset) + '\n')
        write_json(indexpath, index)
        self.print_('Started logging file!')

    def on_save(self):
        logdir, indexpath, relative_filepath = self.get_logpaths()
        index = get_index(indexpath)
        # Abort if the current file isn't in the index (= isn't being logged)
        if relative_filepath not in index:
            return
        logfile = join(logdir, index[relative_filepath])
        wc = self.textarea.get_wordcount()
        lastwc = read_file(logfile).splitlines()[-1].split(';',1)[-1]
        if int(lastwc) == wc:
            return
        data = '{};{}\n'.format(datetime.now(), wc)
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(data)

    def get_logpaths(self):
        """
        Return the different relevant paths.

        logdir             Absolute path to the directory containing the logfiles
        indexpath          Absolute path to the indexfile for all logfiles
        relative_filepath  Relative path to the currently open file in kalpana
        """
        rootdir = fixpath(self.settings['rootdir'])
        logdir = join(rootdir, self.settings['logdir'])
        if not exists(logdir):
            os.makedirs(logdir, mode=0o755, exist_ok=True)
        indexpath = join(logdir, 'index.json')
        relative_filepath = fixpath(self.textarea.file_path).lstrip(rootdir).lstrip(sep)
        return logdir, indexpath, relative_filepath


def get_index(path):
    if exists(path):
        return read_json(path)
    else:
        return {}

def fixpath(p):
    return normcase(normpath(realpath(expanduser(p))))

def generate_logfilename(logroot, pathname):
    default_path = join(logroot, basename(pathname))
    path = default_path
    counter = itertools.count(2)
    while exists(path):
        path = default_path + '-' + str(next(counter))
    return basename(path)
