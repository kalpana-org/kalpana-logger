#!/usr/bin/env python3

from datetime import datetime
from operator import itemgetter
import os
import os.path

from libsyntyche.common import read_json, read_file, local_path, write_file


def formatted_date(datestring):
    return datetime.strptime(datestring, '%Y%m%d').strftime('%d %b %Y')


def format_data(data):
    files = ['{}: {}'.format(name, wc)
             for name, wc in sorted(data.items(), key=itemgetter(1), reverse=True)
             if name != 'total']
    return '<br>'.join(files)


def generate_stats_file(silent):
    config = read_json(os.path.expanduser('~/.config/kalpana/kalpana-logger.conf'))
    logpath = os.path.expanduser(os.path.join(config['rootdir'], config['logdir']))
    logfiles = [os.path.join(logpath,x) for x in os.listdir(logpath)
                if x not in ('index.json', 'stats.html')]
    days = {}

    for log in logfiles:
        lines = read_file(log).splitlines()
        offset = int(lines.pop(0))
        pairs = [(x[:10].replace('-',''), int(x.split(';')[1])) for x in lines]
        for date, wordcount in pairs:
            name = os.path.splitext(os.path.basename(log))[0]
            if date not in days:
                days[date] = {'total': 0, name: 0}
            elif name not in days[date]:
                days[date][name] = 0
            days[date]['total'] += wordcount - offset
            days[date][name] += wordcount - offset
            offset = wordcount

    html = read_file(local_path('statstemplate.html'))
    entry = '<div class="date">{date} - {words}</div><div class="files">{files}</div>'
    out = [entry.format(date=formatted_date(day), words=data['total'], files=format_data(data))
           for day, data in sorted(days.items(), key=itemgetter(0), reverse=True)]
    write_file(os.path.join(logpath, 'stats.html'), html.format('\n'.join(out)))
    # print(*days.items(), sep='\n')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--silent', action='store_true',
                        help="Don't open a browser.")
    args = parser.parse_args()
    generate_stats_file(args.silent)

if __name__ == '__main__':
    main()
