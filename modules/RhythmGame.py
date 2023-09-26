import pygame
import os
from modules.Music.Song import Song

# Constants for the game window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
ARROW_SPEED = 5  # Adjust this to control the arrow speed
ARROW_WIDTH = 50
ARROW_HEIGHT = 20

class RhythmGame:
    def __init__(self, song: Song):
        pygame.init()
        self.song = song
        self.song.load_charts()
        self.clock = pygame.time.Clock()
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Rhythm Game - {self.song.name}")
        self.arrows = []  # List to store arrow positions
        self.load_arrows()
        self.current_arrow_index = 0
        self.score = 0

    def load_arrows(self):
        # Parse the song's note data and create arrow objects
        # Assume the first chart
        chart = self.song.charts[3]
        for note_row in chart.notes:
            for i, note in enumerate(note_row):
                if note == "1":
                    arrow = Arrow(i * 50 + 100, 0)  # Adjust position as needed
                    self.arrows.append(arrow)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear the screen
            self.window.fill(WHITE)

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
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self):
        self.y += ARROW_SPEED

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
