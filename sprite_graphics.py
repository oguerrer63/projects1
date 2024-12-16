# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import os
import board
import displayio

cwd = ("/" + __file__).rsplit("/", 1)[
    0
]  # the current working directory (where this file is)

spritesheet = cwd + "/santa_final.bmp"
scroll_delay = 0.03


class Sprite_Graphics(displayio.Group):
    def __init__(
            self,
            display,
    ):
        super().__init__()
        self.display = display

        splash = displayio.Group()

        # CircuitPython 7+ compatible
        sprite = displayio.OnDiskBitmap(spritesheet)
        bg_sprite = displayio.TileGrid(background, pixel_shader=background.pixel_shader)

        splash.append(bg_sprite)
        display.root_group = splash

        self.root_group = displayio.Group()
        self.root_group.append(self)
        self._icon_group = displayio.Group()
        self.append(self._icon_group)
        
        # Load the icon sprite sheet
        # CircuitPython 7+ compatible
        icons = displayio.OnDiskBitmap(spritesheet)
        self._icon_sprite = displayio.TileGrid(
            icons,
            pixel_shader=icons.pixel_shader,
            tile_width=icon_width,
            tile_height=icon_height
        )
