# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import omni.ui as ui
from omni.ui import color as cl
import asyncio
import omni
import carb

class ProgressBar:
    def __init__(self):
        self.progress_bar_window = None
        self.left = None
        self.right = None
        self._build_fn()

    async def play_anim_forever(self):
        fraction = 0.0
        while True:
            fraction = (fraction + 0.01) % 1.0
            self.left.width = ui.Fraction(fraction)
            self.right.width = ui.Fraction(1.0-fraction)
            await omni.kit.app.get_app().next_update_async()

    def _build_fn(self):
        with ui.VStack():
            self.progress_bar_window = ui.HStack(height=0, visible=False)
            with self.progress_bar_window:
                ui.Label("Processing", width=0, style={"margin_width": 3})
                self.left = ui.Spacer(width=ui.Fraction(0.0))
                ui.Rectangle(width=50, style={"background_color": cl("#76b900")})
                self.right = ui.Spacer(width=ui.Fraction(1.0))

    def show_bar(self, to_show):
        self.progress_bar_window.visible = to_show


