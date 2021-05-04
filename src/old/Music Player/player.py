import bandcampAPI,vlc,os

def playalb(album,beg) :
    track = album.tracks[beg] 
    os.system("""osascript -e 'display notification {track.info["title"]} with title "Now playing"'""")
    player = vlc.MediaPlayer(track.info['file']['mp3-128'])
    player.play()
    player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached,lambda e : playalb(album,beg+1))
    return player
