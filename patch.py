#!/usr/bin/env python3

import argparse
import mmap
import os
import subprocess


def convert_wma_to_wav(game_dir):
    sounds_dir = os.path.join(game_dir, 'sounds')

    for filename in os.listdir(sounds_dir):
        if not filename.endswith('.wma'):
            continue

        wma_file = os.path.join(sounds_dir, filename)
        wav_file = wma_file[:-3] + 'wav'

        print(f'Converting {filename} to PCM wav')

        subprocess.check_call([
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'error',
            '-y',
            '-i', wma_file,
            wav_file,
        ])


def patch_wma_references(game_dir):
    pac_file = os.path.join(game_dir, 'game.pac')

    with open(pac_file, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0

        while True:
            ext_offset = mm.find(b'.wma', offset)
            if ext_offset < 0:
                break

            end = ext_offset + 4

            # There should be no other references to '.wma' besides quoted
            # filenames
            if mm[end] != ord('"'):
                raise ValueError(f'Unexpected byte at offset 0x{ext_offset:x} '
                                 f'after \'.wma\': {mm[end]:x}')

            # The game's max wma filename length is 22 bytes (with extension)
            begin = mm.rfind(b'"', ext_offset - 18 - 1, ext_offset)
            if begin < 0:
                raise ValueError(f'Cannot find start of filename for '
                                 f'offset 0x{ext_offset:x}')

            filename = mm[begin + 1:end]

            print(f'Patching filename {filename} at offset 0x{ext_offset:x} '
                  '(wma -> wav)')
            mm[ext_offset:ext_offset + 4] = b'.wav'

            offset = ext_offset + 4


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('game_dir', help='Path to Pac-Man game directory')
    return parser.parse_args()


def main():
    args = parse_args()

    convert_wma_to_wav(args.game_dir)
    patch_wma_references(args.game_dir)


if __name__ == '__main__':
    main()
