import os
import tkinter as tk
from tkinter import filedialog
import pygame
from modules.Music.Group import Group
from modules.Music.Song import Song
from modules.utils.FileUtils import find_songs
from modules.utils.Loggers import configure_console_logger
import logging

configure_console_logger()
logger = logging.getLogger(__name__)

# Initialize pygame mixer
pygame.mixer.init()


class SongPlayerApp:
    def __init__(self, root):
        self.root = root
        root.title("Song Player")

        # Initialize song data
        self.groups = []
        self.selected_group_index = None
        self.selected_song_index = None

        # Create and configure the main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(padx=10, pady=10)

        # Create and configure the group selection frame
        self.group_frame = tk.Frame(self.main_frame)
        self.group_frame.pack(side=tk.LEFT)

        self.group_label = tk.Label(self.group_frame, text="Groups:")
        self.group_label.pack()

        self.group_listbox = tk.Listbox(self.group_frame, selectmode=tk.SINGLE)
        self.group_listbox.pack()

        self.group_select_button = tk.Button(self.group_frame, text="Select Directory", command=self.select_directory)
        self.group_select_button.pack()

        self.group_listbox.bind("<<ListboxSelect>>", self.select_group)

        # Create and configure the song selection frame
        self.song_frame = tk.Frame(self.main_frame)
        self.song_frame.pack(side=tk.RIGHT)

        self.song_label = tk.Label(self.song_frame, text="Songs:")
        self.song_label.pack()

        self.song_listbox = tk.Listbox(self.song_frame, selectmode=tk.SINGLE)
        self.song_listbox.pack()

        self.play_button = tk.Button(self.song_frame, text="Play Song", command=self.play_song)
        self.play_button.pack()

        self.song_listbox.bind("<<ListboxSelect>>", self.select_song_from_listbox)

    def load_songs(self, root_directory):
        self.groups = find_songs(root_directory)
        total_songs = sum(len(group.songs) for group in self.groups)
        logger.info(f"Found {total_songs} songs in {len(self.groups)} groups.")
        for group in self.groups:
            logger.info(f"Group: {group.name}, Songs: {len(group.songs)}")

    def select_directory(self):
        directory = filedialog.askdirectory(initialdir="./songs", title="Select Song Root Directory")
        if directory:
            self.load_songs(directory)
            self.update_group_list()

    def update_group_list(self):
        self.group_listbox.delete(0, tk.END)
        for group in self.groups:
            self.group_listbox.insert(tk.END, group.name)

    def select_group(self, event):
        selected_group_index = self.group_listbox.curselection()
        if selected_group_index:
            self.selected_group_index = selected_group_index[0]
            selected_group = self.groups[self.selected_group_index]
            self.song_listbox.delete(0, tk.END)  # Clear the current songs list
            for song in selected_group.songs:
                self.song_listbox.insert(tk.END, song.name)  # Add songs to the listbox
            self.selected_song_index = None

    def play_song(self):
        if self.selected_group_index is not None and self.selected_song_index is not None:
            selected_group = self.groups[self.selected_group_index]
            if 0 <= self.selected_song_index < len(selected_group.songs):
                selected_song = selected_group.songs[self.selected_song_index]
                logger.info(f"Playing song: {selected_song.name}")
                pygame.mixer.music.load(os.path.join(selected_song.directory, selected_song.audio_file))
                pygame.mixer.music.play()
        else:
            logger.info("No song selected")

    def select_song_from_listbox(self, event):
        selected_song_index = self.song_listbox.curselection()
        if selected_song_index:
            self.selected_song_index = selected_song_index[0]
            logger.info(f"Selected song index: {self.selected_song_index}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SongPlayerApp(root)
    root.mainloop()
