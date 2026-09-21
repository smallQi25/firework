import asyncio
import sys

import pygame  # Keep visible to Pygbag's dependency scanner.

if sys.platform == "emscripten":
    from mobile import run
else:
    from fireworks import run

asyncio.run(run())
