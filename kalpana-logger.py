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
        self.configpath = objects['settings manager'].get_config_directory()
        self.local_path = get_path()
        self.commands = {'l': (self.start_logging, 'Start logging this file (y for offset, n for no offset)')}

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
        if arg not in ('y','n'):
            self.error('Argument should be y/n! (use offset/no offset)')
            return
        # Offset
        if arg == 'y':
            offset = len(re.findall(r'\S+', read_file(self.textarea.file_path)))
        else:
            offset = 0
        # Paths
        logdir, indexpath, rel_fpath = self.get_logpaths()
        index = get_index(indexpath)
        if rel_fpath in index:
            self.error('File already logged!')
            return
        # Init
        logfname = generate_logfilename(logdir, rel_fpath)
        index[rel_fpath] = logfname
        write_file(join(logdir, logfname), str(offset) + '\n')
        write_json(indexpath, index)
        self.print_('Started logging file!')

    def on_save(self):
        logdir, indexpath, rel_fpath = self.get_logpaths()
        index = get_index(indexpath)
        if rel_fpath not in index:
            return
        logfile = join(logdir, index[rel_fpath])
        wc = self.textarea.get_wordcount()
        lastwc = read_file(logfile).splitlines()[-1].split(';',1)[-1]
        if int(lastwc) == wc:
            return
        data = '{};{}\n'.format(datetime.now(), wc)
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(data)

    def get_logpaths(self):
        rootdir = fixpath(self.settings['rootdir'])
        logdir = join(rootdir, self.settings['logdir'])
        if not exists(logdir):
            os.makedirs(logdir, mode=0o755, exist_ok=True)
        indexpath = join(logdir, 'index.json')
        rel_fpath = fixpath(self.textarea.file_path).lstrip(rootdir).lstrip(sep)
        return logdir, indexpath, rel_fpath


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
