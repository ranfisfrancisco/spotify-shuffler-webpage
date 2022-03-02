"""Shuffler Module"""
from typing import List
import random
import math
import logging

class Shuffler:
    '''Utility class containing methods to shuffle list of Spotify track API objects'''

    @staticmethod
    def shuffle_multiple_playlists(playlists: List, recently_played: List, queue_limit=20,
     no_double_artist=False, no_double_album=False, debug=False) -> List:
        '''Shuffle songs from different playlists weighed against what was recently played
         with several optional modifications.

        recently_played -- list of tracks obtained from the Spotify API
         that have been played recently

        no_double_artist -- flag that suggests shuffler should avoid playing
         the same artist back to back. (default: False)

        no_double_album -- flag that suggests shuffler should avoid playing
         the same album back to back. (default: False)

        debug -- flag that writes the shuffled queue to queue.log file'''

        queue = []
        bag_factor = 2 # Put this many songs from each playlist into a bag and select them at random

        for i, _ in enumerate(playlists):
            playlists[i] = Shuffler.shuffle_single_playlist(playlists[i], recently_played,
                no_double_artist=no_double_artist, no_double_album=no_double_album, debug=debug)

        while len(queue) < queue_limit and sum([len(x) for x in playlists]) > 0:
            rand_index = []

            for _ in range(bag_factor):
                rand_index.extend(*range(0, len(playlists)))

            random.shuffle(rand_index)

            for i in rand_index:
                if len(playlists[i]) > 0:
                    queue.append(playlists[i].pop(0))

                if len(queue) >= queue_limit:
                    break

        # Remove Duplicate Tracks based on URI
        queue = list({ track_data['track']['uri'] : track_data for track_data in queue }.values())

        return queue

    @staticmethod
    def shuffle_single_playlist(song_list: List, recently_played: List,
     no_double_artist=False, no_double_album=False, debug=False) -> List:
        '''Shuffle list of songs weighed against what was recently played
         with several optional modifications.

        song_list -- list of tracks obtained from the Spotify API

        recently_played -- list of tracks obtained from the Spotify API
         that have been played recently

        no_double_artist -- flag that suggests shuffler should avoid playing
         the same artist back to back. (default: False)

        no_double_album -- flag that suggests shuffler should avoid playing
         the same album back to back. (default: False)

        debug -- flag that writes the shuffled queue to queue.log file'''

        queue = []
        queue.extend([{'song' : song, 'score': 0, 'recently_played': None} for song in song_list])

        for i, recency_index in enumerate(recently_played):
            for j, queue_track in enumerate(queue):
                if recency_index['track']['uri'] == queue_track['song']['track']['uri']:
                    queue[j]['recently_played'] = i + 1
                    break

        for idx, song_dict in enumerate(queue):
            queue[idx]['score'] = Shuffler.get_score(song_dict)

        queue = sorted(queue, key= lambda x: -x['score'])

        if no_double_artist:
            queue = Shuffler.filter_double_artist(queue)
        elif no_double_album:
            queue = Shuffler.filter_double_album(queue)

        if debug:
            Shuffler.log(queue, recently_played)

        return [x['song'] for x in queue]

    @staticmethod
    def filter_double_artist(queue: List):
        '''Filter queue to avoid the same artist playing twice in a row.

        queue -- list of tracks'''

        for i in range(1, len(queue)-1):
            cur_artist = queue[i]["song"]["track"]["artists"][0]["name"]
            prev_artist = queue[i-1]["song"]["track"]["artists"][0]["name"]

            if cur_artist == prev_artist:
                for j in range(i+1, len(queue)):
                    j_artist = queue[j]["song"]["track"]["artists"][0]["name"]

                    if cur_artist != j_artist:
                        temp = queue[j]
                        queue[j] = queue[i]
                        queue[i] = temp

        return queue

    @staticmethod
    def filter_double_album(queue):
        '''Filter queue to avoid the same album playing twice in a row.

        queue -- list of tracks'''

        for i in range(1, len(queue)-1):
            cur_album = queue[i]["song"]["track"]["album"]["name"]
            prev_album = queue[i-1]["song"]["track"]["album"]["name"]

            if cur_album == prev_album:
                for j in range(i+1, len(queue)):
                    j_artist = queue[j]["song"]["track"]["album"]["name"]

                    if cur_album != j_artist:
                        temp = queue[j]
                        queue[j] = queue[i]
                        queue[i] = temp

        return queue

    @staticmethod
    def get_recency_bias(song_dict):
        '''Get penalty to apply to score based on how recently a song was played.

        song_dict -- dictionary of {'song': json track data, 'score': integer denoting score,
         'recently_played': integer denoting how recently it was played}'''

        if song_dict['recently_played'] is None:
            return 0

        recent_idx = song_dict['recently_played']
        if recent_idx == 0:
            logging.warning('Recent Index should never be 0!')
            return 0

        bias = -500 * math.tanh(20/recent_idx)

        return min(bias, 0)

    @staticmethod
    def get_random():
        '''Get random value to add to song's score.

        song_dict -- dictionary of {'song': json track data, 'score': integer denoting score,
         'recently_played': integer denoting how recently it was played}. Default None.'''

        return random.randint(0, 1000)

    @staticmethod
    def get_score(song_dict):
        '''Assign score to each song to be used in shuffling.

        Arguments:

        song_dict -- dictionary of {'song': json track data, 'score': integer denoting score,
         'recently_played': integer denoting how recently it was played}.
        '''
        score = 0

        score += Shuffler.get_recency_bias(song_dict)
        score += Shuffler.get_random()

        return score

    @staticmethod
    def log(queue, recently_played, filename='queue.log'):
        '''Log the queue and recently played tracks to a file.'''

        with open(filename, 'a',encoding='utf-8') as file:
            file.write('-' * 15)
            file.write('\nRECENTLY PLAYED TRACKS\n')
            for idx, track in enumerate(recently_played):
                file.write(f'{idx+1} | {track["track"]["name"]}\n')

            file.write("\nSHUFFLED LIST\n")
            file.write('Index | Recently Played | Song | Artist\n')

            for idx, queue_track in enumerate(queue):
                recency_index =  queue_track['recently_played']
                if recency_index is None:
                    recency_index = "NA"
                file.write(f'{idx} | {recency_index} | {queue_track["song"]["track"]["name"]} |\
                {queue_track["song"]["track"]["artists"][0]["name"]} \n')
