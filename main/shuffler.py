"""Shuffler Module"""
from typing import List
from random import randint
import math
import logging

class Shuffler:
    '''Utility class containing methods to shuffle list of Spotify track API objects'''

    @staticmethod
    def shuffle(song_list: List, recently_played: List,
     no_double_artist=True, no_double_album=False, debug=False) -> List:
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
            with open('queue.log', 'w',encoding='utf-8') as file:
                file.write('Recently Played | Song | Artist\n')
                for queue_track in queue:
                    recency_index =  queue_track['recently_played']
                    if recency_index is None:
                        recency_index = "NA"
                    file.write(f'{recency_index} | {queue_track["song"]["track"]["name"]} |\
 {queue_track["song"]["track"]["artists"][0]["name"]} \n')

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

        bias = -250 * math.tanh(5/recent_idx) + randint(0, 100)

        return min(bias, 0)

    @staticmethod
    def get_random():
        '''Get random value to add to song's score.

        song_dict -- dictionary of {'song': json track data, 'score': integer denoting score,
         'recently_played': integer denoting how recently it was played}. Default None.'''

        return randint(0, 1000)

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
