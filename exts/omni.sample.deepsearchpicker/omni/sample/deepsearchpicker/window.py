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
import omni.usd
import carb
from .style import gen_ai_style
from .deep_search import deep_search
import asyncio
from pxr import UsdGeom, Usd, Sdf, Gf

class DeepSearchPickerWindow(ui.Window):

    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(title, **kwargs)
        # Models
        self.frame.set_build_fn(self._build_fn)
        self._index = 0
        self._query_results = None
        self._selected_prim = None
        self._prim_path_model = ui.SimpleStringModel()
	
    def _build_fn(self):
        
        async def replace_prim():
            self._index = 0
            ctx = omni.usd.get_context()
            prim_paths = ctx.get_selection().get_selected_prim_paths()
            if len(prim_paths) != 1:
                carb.log_warn("You must select one and only one prim")
                return
            
            prim_path = prim_paths[0]

            stage = ctx.get_stage()
            self._selected_prim = stage.GetPrimAtPath(prim_path)
            query = self._selected_prim.GetAttribute("DeepSearch:Query").Get()

            prop_paths = ["/Projects/simready_content/common_assets/props/",
                          "/NVIDIA/Assets/Isaac/2022.2.1/Isaac/Robots/",
                          "/NVIDIA/Assets/Isaac/2022.1/NVIDIA/Assets/ArchVis/Residential/Furniture/"]

            self._query_results = await deep_search.query_all(query, "omniverse://ov-simready/", paths=prop_paths)

            self._prim_path_model.set_value(prim_path)

        def increment_prim_index():
            if self._query_results is None:
                return 

            self._index = self._index + 1

            if self._index >= len(self._query_results.paths):
                self._index = 0

            self.replace_reference()
            
        def decrement_prim_index():
            if self._query_results is None:
                return

            self._index = self._index - 1

            if self._index <= 0:
                self._index = len(self._query_results.paths) - 1

            self.replace_reference()

        with self.frame:
            with ui.VStack(style=gen_ai_style):
                with ui.HStack(height=0):
                    ui.Spacer()
                    ui.StringField(model=self._prim_path_model, width=365, height=30)
                    ui.Button(name="create", width=30, height=30, clicked_fn=lambda: asyncio.ensure_future(replace_prim()))
                    ui.Spacer()
                with ui.HStack(height=0):
                    ui.Spacer()
                    ui.Button("<", width=200, clicked_fn=lambda: decrement_prim_index())
                    ui.Button(">", width=200, clicked_fn=lambda: increment_prim_index())
                    ui.Spacer()
    
    def replace_reference(self):
        references: Usd.references = self._selected_prim.GetReferences()
        references.ClearReferences()
        references.AddReference(
                assetPath="omniverse://ov-simready" + self._query_results.paths[self._index].uri)

        carb.log_info("Got it?")

    def destroy(self):
        super().destroy()