# video-stegano

A minimal video steganography tool written in python. The project uses a variation of the LSB steganography algorithm to hide an image message in a carrier video file.

## Usage
- Hide an image message in carrier video to create stegano:
```
python -hide [Path to carrier video] [Path to image message]
```

- Retrieve hidden message from stegano video:
```
python -extract [Path to stegano video]
```
Result is saved into ```extracted.png```
