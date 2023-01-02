import board
import audioio
import audiocore
import audiomixer

DEMO, PLAYING, URGENT, CRAZY, COMPLETE, CORRECT = range(6)

class AudioEngine:
    root_path = '/sounds'
    paths = {
        DEMO: "/opening.wav",
        PLAYING: "/playing_1.wav",
        URGENT: "/playing_2.wav",
        CRAZY: "/playing_3.wav",
        COMPLETE: "/complete.wav",
        CORRECT: "/correct.wav",
    }
    currently_playing_state = None
    current_bg_audio = None
    correct_audio_file = None
    correct_wav_data = None

    channel_count = None
    bits_per_sample = None
    sample_rate = None

    def __get_path(self, state):
        return self.root_path + self.paths[state]

    def __init__(self):
        self.voices = 2
        with open(self.__get_path(DEMO), 'rb') as file:
            wav = audiocore.WaveFile(file)
            
            self.channel_count = wav.channel_count
            self.bits_per_sample = wav.bits_per_sample
            self.sample_rate = wav.sample_rate

            print('%d channels, %d bits per sample, %d Hz sample rate ' %
                (wav.channel_count, wav.bits_per_sample, wav.sample_rate))

            file.close()

        self.correct_audio_file = open(self.__get_path(CORRECT), 'rb')
        self.correct_wav_data = audiocore.WaveFile(self.correct_audio_file)

    def __del__(self):
        if self.correct_audio_file is not None:
            self.correct_audio_file.close()
            self.correct_audio_file = None
            self.audio.deinit()

    def initialize_audio(self):
        if self.channel_count == 1:
            return audioio.AudioOut(board.A1)
        elif self.channel_count == 2:
            return audioio.AudioOut(board.A1, right_channel=board.A0)
        else:
            raise RuntimeError('Must be mono or stereo waves!')
    
    def initialize_mixer(self):
        return audiomixer.Mixer(voice_count=2,
                        sample_rate=self.sample_rate,
                        channel_count=self.channel_count,
                        bits_per_sample=self.bits_per_sample,
                        samples_signed=True)
    
    def get_state(self):
        if self.currently_playing_state is None:
            return -1

        return self.currently_playing_state

    def stop_playing_sample(self, mixer):
        if self.current_bg_audio is None:
            return None
        print("Closing file: " + self.current_bg_audio['path'])
        mixer.stop_voice(self.current_bg_audio['voice'])
        self.current_bg_audio['file'].close()

    def handle_audio_for_state(self, state, mixer):
        self.stop_playing_sample(mixer)

        voice = 0
        loop = state is not COMPLETE

        path = self.__get_path(state)
        print("Opening file: " + path)

        file = open(path, 'rb')
        wav = audiocore.WaveFile(file)
        mixer.voice[0].level = 0.25
        mixer.play(wav, voice=voice, loop=loop)
        self.currently_playing_state = state
        self.current_bg_audio = {
            'voice': voice,
            'file': file,
            'path': path
        }

    def play_correct_sound(self, mixer):
        mixer.play(self.correct_wav_data, voice=1, loop=False)