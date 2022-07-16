#!/usr/bin/env python3
"""
Export playlists to M3U files.
"""

import argparse
import pathlib
import os.path
import xml.etree.ElementTree as ET


def _getParsedTraktorCollection(path=None):
    """
    Return a parsed version of the Traktor database
    Automatically tries to guess the location of collection.nml if none is provided.
    From: https://github.com/psobot/traktor
    """
    if path:
        if not os.path.exists(path):
            raise Exception("Provided database file not found! (at %s)" % path)
    else:
        #   Try-to-find-database-file mode
        #   For example, mine's at: "~/Documents/Native Instruments/Traktor 2.0.3/collection.nml"
        #   Start reading at ~ and try to recurse down there.
        path = os.path.expanduser("~/Documents/Native Instruments/")
        if os.path.exists(path):
            traktorFolder = None
            for folder in os.listdir(path):  # Returns subfolders in order
                if folder.startswith("Traktor"):  # Therefore latest version of Traktor will always be first
                    traktorFolder = folder
            if traktorFolder:
                path += traktorFolder + "/collection.nml"
                if not os.path.exists(path):
                    raise Exception("collections.nml file not found!" )
            else:
                raise Exception("Traktor preferences folder not found!")
        else:
            raise Exception("Native Instruments preferences folder not found!")

    print(f'Found collection at {path}')
    collection = ET.parse(path)
    return collection.getroot()


def getPlaylists():
    pass


def get_parser():
    parser = argparse.ArgumentParser(description='Traktor playlist exporter')
    parser.add_argument('-f',
                        '--folder',
                        nargs='?',
                        default='./playlists',
                        type=pathlib.Path,
                        help='The folder where exported playlists will be placed')
    parser.add_argument('-c',
                        '--collection',
                        nargs='?',
                        default=None,
                        type=pathlib.Path,
                        help='The path to your Traktor collection.nml')
    parser.add_argument('-u',
                        '--upload',
                        default=False,
                        help='When finished creating playlists, upload them',
                        action='store_true')
    return parser


def upload(outputPath):
    glob_path = os.path.join(outputPath, '*.m3u')

    command = f'rsync -avhrPt -e "ssh -T -o Compression=no -x" {glob_path} ideas:/Users/Shared/Playlists/'
    print(f'Uploading playlists: {command}')
    os.system(command)


def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args())

    main(args['collection'], args['folder'])
    if(args['upload']):
        upload(args['folder'])


def main(inputFile, outputPath):
    if os.path.exists(outputPath):
        glob_m3u = os.path.join(outputPath, '*.m3u')
        os.system(f'trash {glob_m3u}')  # could be `rm -rf {glob_m3u}` if you like ;)
    else:
        os.mkdir(outputPath)

    traktor = _getParsedTraktorCollection(path=inputFile)

    for node in traktor.iterfind('PLAYLISTS/NODE/SUBNODES/NODE[@TYPE="PLAYLIST"]'):
        name = node.get('NAME')
        if name in ['_LOOPS', '_RECORDINGS', 'Preparation']:
            continue

        outputFile = os.path.join(outputPath, name.replace(os.sep, '-').strip() + '.m3u')

        print(f'Writing {outputFile}')
        with open(outputFile, 'w') as file:
            for track in node.iterfind('PLAYLIST/ENTRY/PRIMARYKEY[@TYPE="TRACK"]'):
                path = track.get('KEY').replace('/:', os.sep)
                path = path if path[1] == ':' else os.path.join(os.sep, 'Volumes', path)
                path = path.replace('/Volumes/Gleitzpod', '/Volumes/RuseVault/Gleitz')

                file.write(path + '\n')

if __name__ == '__main__':
    command_line_runner()
