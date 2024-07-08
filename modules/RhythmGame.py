import pygame
import os
from modules.Music.Song import Song
from typing import List, Optional

# Constants for the game window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
ARROW_WIDTH = 50
ARROW_HEIGHT = 1
ARROW_SPEED = 10
HORIZONTAL_SPACING = 100  # Horizontal spacing between note lanes


class Arrow:
    def __init__(self, x: int, y: int, spawn_time: float):
        self.x = x
        self.y = y
        self.spawn_time = spawn_time

    def move(self):
        self.y -= ARROW_SPEED  # Move upwards

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.x, self.y, ARROW_WIDTH, ARROW_HEIGHT))


class MeasureLine:
    def __init__(self, x: int, speed: int):
        self.x = x
        self.y = WINDOW_HEIGHT
        self.speed = speed

    def move(self):
        self.y -= self.speed

    def draw(self, surface):
        pygame.draw.rect(surface, (0, 0, 255), (0, self.y, WINDOW_WIDTH, 2))


class BeatInfo:
    def __init__(self, time: float, normalized_time: float, arrows: Optional[List[Arrow]] = None):
        self.time = time
        self.normalized_time = normalized_time
        self.arrows = arrows if arrows else []


class RhythmGame:
    def __init__(self, song: Song):
        pygame.init()
        pygame.mixer.init()
        self.clap_sound = pygame.mixer.Sound(r"..\assets\clap.ogg")
        self.song = song
        self.song.load_charts()
        self.clock = pygame.time.Clock()
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Rhythm Game - {self.song.name}")
        self.arrows = []  # List to store arrow positions
        self.measure_lines = []  # List to store measure lines
        self.current_arrow_index = 0
        self.current_measure_line_index = 0
        self.current_beat_index = 0  # Initialize current_beat_index
        self.score = 0
        self.song_start_time = None  # Time when the song started
        self.first_measure_despawned = False
        self.init_bpm()
        self.init_chart()
        self.precalculate_times()

    def init_bpm(self):
        self.current_bpm = None
        self.next_bpm_change = None
        if self.song.bpms:
            self.current_bpm = self.song.bpms[0][1]
            if len(self.song.bpms) > 1:
                self.next_bpm_change = self.song.bpms[1][0]

    def init_chart(self):
        self.current_chart = self.song.charts[3]  # Hardcoding 3 for now
        self.current_chart_index = 0
        self.current_measure = 0
        self.measure_duration = 0
        self.measures = self.current_chart.measures  # Get the measures from the chart
        self.measure_start_time = 0.0  # Time when the current measure started
        self.beat_start_time = 0.0  # Time when the current beat started

    def get_song_time(self) -> float:
        if self.song_start_time is None:
            self.song_start_time = pygame.time.get_ticks()
        return (pygame.time.get_ticks() - self.song_start_time) / 1000.0

    def precalculate_times(self):
        """
        Pre-calculate the spawn times for measures and beats.
        """
        self.measure_times = []
        self.beat_times = []

        total_song_duration = self.song.duration  # Assuming the song object has a duration attribute in seconds

        time = 0.0
        measure_index = 0
        while measure_index < len(self.measures):
            self.measure_times.append(time)
            measure = self.measures[measure_index]
            time_per_beat = (4 * 60 / self.current_bpm) / len(measure)  # 4 beats per measure
            for beat in measure:
                arrows = []
                for i, note in enumerate(beat):
                    if note == "1":
                        x = i * HORIZONTAL_SPACING + 100  # Adjust horizontal spacing here
                        arrow = Arrow(x, WINDOW_HEIGHT - ARROW_HEIGHT, time)
                        arrows.append(arrow)
                normalized_time = time / total_song_duration
                self.beat_times.append(BeatInfo(time, normalized_time, arrows))
                time += time_per_beat
            measure_index += 1
        return

    def update_song_time(self):
        """
        Call this once per frame, at the FPS framerate.
        :return:
        """
        self.song_time = self.get_song_time()

        if self.measure_times and self.song_time >= self.measure_times[0]:
            self.measure_times.pop(0)
            x = self.current_measure_line_index * HORIZONTAL_SPACING + 100
            measure_line = MeasureLine(x, ARROW_SPEED)
            self.measure_lines.append(measure_line)
            self.current_measure_line_index += 1

        if self.beat_times and self.song_time >= self.beat_times[0].time:
            beat_info = self.beat_times.pop(0)
            self.arrows.extend(beat_info.arrows)

            self.current_beat_index += 1
            if self.current_beat_index >= len(self.measures[self.current_measure]):
                self.current_beat_index = 0
                self.current_measure += 1

    def remove_past_arrows(self):
        before_len = len(self.arrows)
        self.arrows = [arrow for arrow in self.arrows if arrow.y > -ARROW_HEIGHT]
        after_len = len(self.arrows)
        if before_len > after_len:
            # Play clap sound when arrows are removed
            self.clap_sound.play()

    def remove_past_measure_lines(self):
        self.measure_lines = [line for line in self.measure_lines if line.y > 0]
        if not self.first_measure_despawned and len(self.measure_lines) == 0:
            self.first_measure_despawned = True
            pygame.mixer.music.play()

    def run(self):
        # Load and set up the music
        pygame.mixer.music.load(os.path.join(self.song.directory, self.song.audio_file))
        pygame.mixer.music.set_volume(1.0)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear the screen
            self.window.fill(WHITE)

            self.update_song_time()

            # Remove arrows that have gone off the screen
            self.remove_past_arrows()

            # Remove measure lines that have gone off the screen
            self.remove_past_measure_lines()

            # Move and draw arrows
            for arrow in self.arrows:
                arrow.move()
                arrow.draw(self.window)

            # Move and draw measure lines
            for measure_line in self.measure_lines:
                measure_line.move()
                measure_line.draw(self.window)

            # Update the display
            pygame.display.flip()

            # Control the game speed
            self.clock.tick(FPS)

    def start(self):
        self.run()
        pygame.quit()


if __name__ == "__main__":
    selected_song = Song(name="bass 2 bass",
                         audio_file="bass 2 bass.ogg",
                         sm_file="bass 2 bass.sm",
                         directory=os.path.abspath("../songs/DDR A/bass 2 bass"),
                         id=0)

    game = RhythmGame(selected_song)
    game.start()
