# library-lightbox

WAV files should start and end with the sample 0x08_00 (4 bytes after the ``data`` identifier and the final sample) and be encoded as mono, 16kHz (use ``ffmpeg -i <source file> -ac 1 -ar 16000 <output file.wav>``)

BMP files should be 16x16, with transparent areas replaced with 0x00_00_FF