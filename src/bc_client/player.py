import vlc


class Player:
    def __init__(self):
        self.playlist = list()
        self.list_player = vlc.MediaListPlayer()
        self.player = self.list_player.get_media_player()
        self.playlist = vlc.MediaList()
        self.total_time = lambda: int(self.player.get_length() / 1000)
        self.time = lambda: int(self.player.get_time() / 1000)
        self.pause = self.player.pause
        self.playing = self.player.is_playing

    def play_list(self, playlist):
        self.playlist = vlc.MediaList()
        for song in playlist:
            self.playlist.add_media(vlc.Media(song))
        self.list_player.set_media_list(self.playlist)
        self.player.stop()
        self.list_player.play()
