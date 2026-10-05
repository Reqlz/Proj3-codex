# Add your own music

Nothing is uploaded. Music plays directly from this folder on your computer.

1. Copy an `.ogg`, `.mp3`, or `.wav` music file into this folder. For example, `night-garden.ogg`.
2. Open `playlist.json` in your editor and replace the empty list with its filename:

   ```json
   {
     "tracks": ["night-garden.ogg"]
   }
   ```

3. Start the game and open **Settings → Audio → Reload playlist**.
4. Enable music and set your volume. Use Pause or Next to control playback.

## A small practice exercise

Add a second track, such as `starlight.mp3`, and edit the configuration:

```json
{
  "tracks": [
    "night-garden.ogg",
    "starlight.mp3"
  ]
}
```

Keep the double quotes around filenames. Separate entries with a comma, but do not put a comma after the last entry. Use exact filenames, including their extensions. Do not paste the Markdown backticks into the JSON file.

Reload the playlist. With Shuffle disabled, the tracks play in this order and repeat. Swap the two lines to reverse their order, then reload again. Try adjusting the volume while music is playing.

The example files are not included; substitute files you have on your computer. Missing files, malformed JSON, and unavailable audio hardware appear as messages in Settings and do not stop the game. Subfolders inside this music directory are allowed; files outside it are not.
