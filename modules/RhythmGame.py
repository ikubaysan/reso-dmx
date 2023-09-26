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

    def init_bpm(self):
        self.current_bpm = None
        self.next_bpm_change = None
        if self.song.bpms:
            self.current_bpm = self.song.bpms[0][1]
            if len(self.song.bpms) > 1:
                self.next_bpm_change = self.song.bpms[1][0]

    def load_arrows(self):
        chart = self.song.charts[0]  # Adjust the chart index as needed
        for note_row in chart.notes:
            for i, note in enumerate(note_row):
                if note == "1":
                    x = i * HORIZONTAL_SPACING + 100  # Adjust horizontal spacing here
                    arrow = Arrow(x, WINDOW_HEIGHT - ARROW_HEIGHT, self.song_time)
                    self.arrows.append(arrow)

    def update_song_time(self):
        if self.current_bpm:
            self.song_time += 1 / (self.current_bpm / 60) / FPS  # Increment song time based on current BPM

            if self.next_bpm_change and self.song_time >= self.next_bpm_change:
                self.current_bpm = self.song.bpms[1][1]
                if len(self.song.bpms) > 2:
                    self.next_bpm_change = self.song.bpms[2][0]
                else:
                    self.next_bpm_change = None

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear the screen
            self.window.fill(WHITE)

            self.update_song_time()

            # Move and draw arrows
            for arrow in self.arrows:
                arrow.move()
                arrow.draw(self.window)

            # Update the display
            pygame.display.flip()

            # Control the game speed
            self.clock.tick(FPS)

    def start(self):
        self.load_arrows()
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
    selected_song = Song(name="Bad Apple",
                         audio_file="Bad Apple!! feat. nomico.ogg",
                         sm_file="Bad Apple!! feat. nomico.sm",
                         directory=r"C:\Users\Tay\Desktop\Stuff\Coding\Repos\my_github\reso-dmx\songs\DDR A\Bad Apple!! feat. nomico")
    game = RhythmGame(selected_song)
    game.start()
