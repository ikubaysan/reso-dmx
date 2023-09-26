import pygame
import os
from modules.Music.Song import Song

# Constants for the game window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
ARROW_WIDTH = 50
ARROW_HEIGHT = 20
ARROW_SPEED = 5
HORIZONTAL_SPACING = 100  # Adjust this value to control horizontal spacing

class RhythmGame:
    def __init__(self, song: Song):
        pygame.init()
        self.song = song
        self.song.load_charts()
        self.clock = pygame.time.Clock()
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Rhythm Game - {self.song.name}")
        self.arrows = []  # List to store arrow positions
        self.current_arrow_index = 0
        self.score = 0
        self.song_time = 0.0  # Current song time in seconds
        self.init_bpm()
        self.init_chart()

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

    def update_song_time(self):
        if self.current_bpm:
            self.song_time += 1 / (self.current_bpm / 60) / FPS  # Increment song time based on current BPM

            if self.next_bpm_change and self.song_time >= self.next_bpm_change:
                self.current_bpm = self.song.bpms[1][1]
                if len(self.song.bpms) > 2:
                    self.next_bpm_change = self.song.bpms[2][0]
                else:
                    self.next_bpm_change = None

            # Check if it's time to move to the next measure
            if self.song_time >= self.measure_start_time + self.measure_duration:
                self.current_measure += 1
                if self.current_measure < len(self.measures):
                    self.measure_duration = len(self.measures[self.current_measure]) * (60 / self.current_bpm)
                    self.measure_start_time = self.song_time

    def spawn_arrows(self):
        if self.current_measure < len(self.measures):
            measure = self.measures[self.current_measure]
            beats_in_measure = len(measure)
            time_per_beat = (60 / self.current_bpm) / beats_in_measure

            current_beat_index = int((self.song_time - self.measure_start_time) / time_per_beat)

            if current_beat_index < beats_in_measure:
                current_beat = measure[current_beat_index]
                for i, note in enumerate(current_beat):
                    if note == "1":
                        x = i * HORIZONTAL_SPACING + 100  # Adjust horizontal spacing here
                        arrow = Arrow(x, WINDOW_HEIGHT - ARROW_HEIGHT, self.song_time)
                        self.arrows.append(arrow)

    def remove_past_arrows(self):
        self.arrows = [arrow for arrow in self.arrows if arrow.y > -ARROW_HEIGHT]

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear the screen
            self.window.fill(WHITE)

            self.update_song_time()

            # Spawn new arrows based on song time and BPM
            self.spawn_arrows()

            # Remove arrows that have gone off the screen
            self.remove_past_arrows()

            # Move and draw arrows
            for arrow in self.arrows:
                arrow.move()
                arrow.draw(self.window)

            # Update the display
            pygame.display.flip()

            # Control the game speed
            self.clock.tick(FPS)

    def start(self):
        self.run()
        pygame.quit()

class Arrow:
    def __init__(self, x, y, spawn_time):
        self.x = x
        self.y = y
        self.spawn_time = spawn_time

    def move(self):
        self.y -= ARROW_SPEED  # Move upwards

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.x, self.y, ARROW_WIDTH, ARROW_HEIGHT))

if __name__ == "__main__":
    # Replace with the actual Song object
    selected_song = Song(name="bass 2 bass",
                         audio_file="bass 2 bass.ogg",
                         sm_file="bass 2 bass.sm",
                         directory=r"C:\Users\Tay\Desktop\Stuff\Coding\Repos\my_github\reso-dmx\songs\DDR A\bass 2 bass")
    game = RhythmGame(selected_song)
    game.start()
