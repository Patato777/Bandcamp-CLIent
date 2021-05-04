import vlc

class Player:
    def __init__(self):
        self.player = vlc.MediaPlayer()
        self.playing = self.player.is_playing

    def play(self, file):
        self.media = vlc.Media(file)
        self.player.set_media(self.media)
        self.player.play()

    def pause(self, toggle=True):
        if self.player.can_pause() and (toggle or self.playing()):
            self.player.pause()

    def resume(self):
        if self.player.can_pause() and not self.player.playing():
            self.player.pause()
