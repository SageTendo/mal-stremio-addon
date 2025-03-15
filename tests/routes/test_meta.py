import unittest

from app.routes.meta import kitsu_to_meta
from run import app

KITSU_RESPONSE = {
    "meta": {"id": "kitsu:9969", "kitsu_id": "9969", "type": "series", "animeType": "TV", "name": "Death Parade",
             "slug": "death-parade", "aliases": ["Death Parade"],
             "genres": ["Mystery", "Psychological", "Thriller", "Game", "Drama"],
             "logo": "https://assets.fanart.tv/fanart/tv/289177/hdtvlogo/death-parade-54c1677b81e69.png",
             "poster": "https://media.kitsu.app/anime/poster_images/9969/medium.jpg",
             "background": "https://assets.fanart.tv/fanart/tv/289177/showbackground/death-parade-5ea09b8751828.jpg",
             "description": "After death, there is no heaven or hell, only a bar that stands between reincarnation and "
                            "oblivion. There the attendant will, one after another, challenge pairs of the recently "
                            "deceased to a random game in which their fate of either ascending into reincarnation or "
                            "falling into the void will be wagered. Whether it's bowling, darts, air hockey, or "
                            "anything in between, each person's true nature will be revealed in a ghastly parade of "
                            "death and memories, dancing to the whims of the bar's master. Welcome to Quindecim, where "
                            "Decim, arbiter of the afterlife, awaits!\n\nDeath Parade expands upon the original "
                            "one-shot intended to train young animators. It follows yet more people receiving "
                            "judgment—until a strange, black-haired guest causes Decim to begin questioning his "
                            "own rulings.",
             "releaseInfo": "2015", "year": "2015", "imdbRating": "8.2", "userCount": 123404, "status": "finished",
             "runtime": "23 min", "trailers": [{"source": "O1X6czI74UQ", "type": "Trailer"}], "videos": [
            {"id": "kitsu:9969:1", "title": "Death Seven Darts", "released": "2015-01-10T03:00:00.000Z", "season": 1,
             "episode": 1, "thumbnail": "https://episodes.metahub.space/tt4279012/1/1/w780.jpg",
             "overview": "A young couple, Takashi and Machiko, arrive in the bar Quindecim without any recollection of "
                         "how they got there. The bartender tells them they cannot leave until they first finish "
                         "playing a game, one in which their lives will be at stake.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 1},
            {"id": "kitsu:9969:2", "title": "Death Reverse", "released": "2015-01-17T03:00:00.000Z", "season": 1,
             "episode": 2, "thumbnail": "https://episodes.metahub.space/tt4279012/1/2/w780.jpg",
             "overview": "A black-haired woman awakens in an unfamiliar place, unable to remember even her own name. "
                         "She is taken by a girl named Nona to Quindecim, "
                         "where she is told that she will be an assistant, and is instructed as to the purpose of the "
                         "bar's existence.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 2},
            {"id": "kitsu:9969:3", "title": "Rolling Ballade", "released": "2015-01-24T03:00:00.000Z", "season": 1,
             "episode": 3, "thumbnail": "https://episodes.metahub.space/tt4279012/1/3/w780.jpg",
             "overview": "College student Shigeru Miura wakes up in Quindecim, and falls in love at first sight with "
                         "the woman at the bar. Unable to remember even her own name, the woman asks him to play a "
                         "game with her, after being assured that it will jog her memory.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 3},
            {"id": "kitsu:9969:4", "title": "Death Arcade", "released": "2015-01-31T03:00:00.000Z", "season": 1,
             "episode": 4, "thumbnail": "https://episodes.metahub.space/tt4279012/1/4/w780.jpg",
             "overview": "TV personality Misaki Tachibana is convinced that she is in Quindecim as part of a "
                         "hidden-camera TV show, and enlists her counterpart, Yousuke Tateishi, to help her "
                         "liven the show up. Decim takes measures to ensure extreme conditions for the contestants.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 4},
            {"id": "kitsu:9969:5", "title": "Death March", "released": "2015-02-07T03:00:00.000Z", "season": 1,
             "episode": 5, "thumbnail": "https://episodes.metahub.space/tt4279012/1/5/w780.jpg",
             "overview": "Two more people - a young boy and an older man - arrive at Quindecim, but this time, "
                         "Decim senses something out of place. Before Decim can explain the game to the pair, the "
                         "older man reveals that he remembers having seen Decim and the bar before!",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 5},
            {"id": "kitsu:9969:6", "title": "Cross Heart Attack", "released": "2015-02-14T03:00:00.000Z", "season": 1,
             "episode": 6, "thumbnail": "https://episodes.metahub.space/tt4279012/1/6/w780.jpg",
             "overview": "A high-school girl named Mayu arrives at a Japanese-style bar being tended by Ginti. "
                         "He demands that she play a game against the man in the bar, who she instantly recognizes as "
                         "Harada, of the boy idol band C.H.A, and she eagerly accepts.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 6},
            {"id": "kitsu:9969:7", "title": "Alcohol Poison", "released": "2015-02-21T03:00:00.000Z", "season": 1,
             "episode": 7, "thumbnail": "https://episodes.metahub.space/tt4279012/1/7/w780.jpg",
             "overview": "When the black-haired woman stumbles upon a picture book, she asks Decim about it, "
                         "and he tells her that it might belong to Quin, Quindecim's previous bartender. "
                         "Decim reveals the reasons why he spends so much time putting together mannequins.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 7},
            {"id": "kitsu:9969:8", "title": "Death Rally", "released": "2015-02-28T03:00:00.000Z", "season": 1,
             "episode": 8, "thumbnail": "https://episodes.metahub.space/tt4279012/1/8/w780.jpg",
             "overview": "Prior to the arrival of a pair of guests--a police detective and young man "
                         "raising his sister--Decim wonders if there has been a mistake, since the memories he has "
                         "received are those of a killer. But despite his protestations, Nona prods him to continue.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 8},
            {"id": "kitsu:9969:9", "title": "Death Counter", "released": "2015-03-07T03:00:00.000Z", "season": 1,
             "episode": 9, "thumbnail": "https://episodes.metahub.space/tt4279012/1/9/w780.jpg",
             "overview": "As the two contestants continue their game, Shimada is surprised to learn that Detective "
                         "Tatsumi is sympathetic to his desire for revenge against his sister's attacker. "
                         "The black-haired woman is troubled by how far Decim is willing to go.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 9},
            {"id": "kitsu:9969:10", "title": "Story Teller", "released": "2015-03-14T03:00:00.000Z", "season": 1,
             "episode": 10, "thumbnail": "https://episodes.metahub.space/tt4279012/1/10/w780.jpg",
             "overview": "Decim visits Nona and tells her that he believes that their way of passing judgment "
                         "is flawed. Nona sends him another customer, whose case may unravel the mystery of the "
                         "black-haired woman, and whom Decim chooses to judge without the aid of any memories.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 10},
            {"id": "kitsu:9969:11", "title": "Memento Mori", "released": "2015-03-21T03:00:00.000Z", "season": 1,
             "episode": 11, "thumbnail": "https://episodes.metahub.space/tt4279012/1/11/w780.jpg",
             "overview": "Mayu is given a chance to spare Harada's soul from the void, for a price. With Chiyuki's "
                         "judgment pending, she revisits her love of ice skating, with the hope that the memories she "
                         "recovers will help her to come to terms with her passing.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 11},
            {"id": "kitsu:9969:12", "title": "Suicide Tour", "released": "2015-03-28T03:00:00.000Z", "season": 1,
             "episode": 12, "thumbnail": "https://episodes.metahub.space/tt4279012/1/12/w780.jpg",
             "overview": "Oculus confronts Nona concerning Decim, demanding to know what she has done to him. Chiyuki "
                         "awakens in her house the living world again to find that Decim has brought her there to "
                         "offer her the chance to reclaim her life.",
             "imdb_id": "tt4279012", "imdbSeason": 1, "imdbEpisode": 12}],
             "links": [{"name": "8.2", "category": "imdb", "url": "https://kitsu.io/anime/death-parade"},
                       {"name": "Mystery", "category": "Genres",
                        "url": "stremio:///discover/https%3A%2F%2Fanime-kitsu.strem.fun%2Fmanifest.json"
                               "/anime/kitsu-anime-popular?genre=Mystery"},
                       {"name": "Psychological", "category": "Genres",
                        "url": "stremio:///discover/https%3A%2F%2Fanime-kitsu.strem.fun%2Fmanifest.json"
                               "/anime/kitsu-anime-popular?genre=Psychological"},
                       {"name": "Thriller", "category": "Genres",
                        "url": "stremio:///discover/https%3A%2F%2Fanime-kitsu.strem.fun%2Fmanifest.json"
                               "/anime/kitsu-anime-popular?genre=Thriller"},
                       {"name": "Game", "category": "Genres",
                        "url": "stremio:///discover/https%3A%2F%2Fanime-kitsu.strem.fun%2Fmanifest.json"
                               "/anime/kitsu-anime-popular?genre=Game"},
                       {"name": "Drama", "category": "Genres",
                        "url": "stremio:///discover/https%3A%2F%2Fanime-kitsu.strem.fun%2Fmanifest.json"
                               "/anime/kitsu-anime-popular?genre=Drama"}],
             "imdb_id": "tt4279012"}, "cacheMaxAge": 43200}


class TestMeta(unittest.TestCase):
    def setUp(self):
        """Set up the Flask test client"""
        app.config['TESTING'] = True
        app.config['SECRET'] = "Testing Secret"
        self.client = app.test_client()

    def test_meta(self):
        """Test the /meta endpoint"""
        response = self.client.get('123/someParameters/meta/series/mal_28223.json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json

        self.assertIn('meta', response_data)
        for key in response_data['meta']:
            self.assertIsNotNone(response_data['meta'][key])

        expected = kitsu_to_meta(KITSU_RESPONSE)
        for key in expected:
            self.assertEqual(expected[key], response_data['meta'][key])
