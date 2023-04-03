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
import asyncio
import omni.kit.commands
from omni.kit.window.popup_dialog.form_dialog import FormDialog
from .utils import CreateCubeFromCurve
from .style import gen_ai_style, guide
from .chatgpt_apiconnect import call_Generate
from .priminfo import PrimInfo
from pxr import Sdf
from .widgets import ProgressBar

class GenAIWindow(ui.Window):

    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(title, **kwargs)
        # Models
        self._path_model = ui.SimpleStringModel()
        self._prompt_model = ui.SimpleStringModel("generate warehouse objects")
        self._area_name_model = ui.SimpleStringModel()
        self._use_deepsearch = ui.SimpleBoolModel()
        self._use_chatgpt = ui.SimpleBoolModel()
        self._areas = []
        self.response_log = None
        self.current_index = -1
        self.current_area = None
        self._combo_changed_sub = None
        self.frame.set_build_fn(self._build_fn)
	
    def _build_fn(self):
        with self.frame:
            with ui.ScrollingFrame():
                with ui.VStack(style=gen_ai_style):
                    with ui.HStack(height=0):
                        ui.Label("Content Generatation with ChatGPT", style={"font_size": 18})
                        ui.Button(name="properties", tooltip="Configure API Key and Nucleus Path", width=30, height=30, clicked_fn=lambda: self._open_settings())
                        
                    with ui.CollapsableFrame("Getting Started Instructions", height=0, collapsed=True):
                        ui.Label(guide, word_wrap=True)
                    ui.Line()
                    with ui.HStack(height=0):
                        ui.Label("Area Name", width=ui.Percent(30))
                        ui.StringField(model=self._area_name_model)
                        ui.Button(name="create", width=30, height=30, clicked_fn=lambda: self._create_new_area(self.get_area_name()))
                    with ui.HStack(height=0):
                        ui.Label("Current Room", width=ui.Percent(30))
                        self._build_combo_box()
                    ui.Line()
                    with ui.HStack(height=ui.Percent(50)):
                        ui.Label("Prompt", width=0)
                        ui.StringField(model=self._prompt_model, multiline=True)
                    ui.Line()
                    self._build_ai_section()
    
    def _save_settings(self, dialog):
        values = dialog.get_values()
        carb.log_info(values)

        settings = carb.settings.get_settings()
        settings.set_string("/persistent/exts/omni.example.airoomgenerator/APIKey", values["APIKey"])
        settings.set_string("/persistent/exts/omni.example.airoomgenerator/deepsearch_nucleus_path", values["deepsearch_nucleus_path"])
        settings.set_string("/persistent/exts/omni.example.airoomgenerator/path_filter", values["path_filter"])

        dialog.hide()

    def _open_settings(self):
        settings = carb.settings.get_settings()   
        apikey_value = settings.get_as_string("/persistent/exts/omni.example.airoomgenerator/APIKey")
        nucleus_path = settings.get_as_string("/persistent/exts/omni.example.airoomgenerator/deepsearch_nucleus_path")
        path_filter = settings.get_as_string("/persistent/exts/omni.example.airoomgenerator/path_filter")

        if apikey_value == "":
            apikey_value = "Enter API Key Here"
        if nucleus_path == "":
            nucleus_path = "(ENTERPRISE ONLY) Enter Nucleus Path Here"
        if path_filter == "":
            path_filter = ""

        field_defs = [
            FormDialog.FieldDef("APIKey", "API Key: ", ui.StringField, apikey_value),
            FormDialog.FieldDef("deepsearch_nucleus_path", "Nucleus Path: ", ui.StringField, nucleus_path),
            FormDialog.FieldDef("path_filter", "Path Filter: ", ui.StringField, path_filter)
        ]        

        dialog = FormDialog(
            title="Settings",
            message="Your Settings: ",
            field_defs = field_defs,
            ok_handler=lambda dialog: self._save_settings(dialog))

        dialog.show()

    def _build_ai_section(self):
        with ui.HStack(height=0):
            ui.Spacer()
            ui.Label("Use ChatGPT: ")
            ui.CheckBox(model=self._use_chatgpt)
            ui.Label("Use Deepsearch: ", tooltip="ENTERPRISE USERS ONLY")
            ui.CheckBox(model=self._use_deepsearch)
            ui.Spacer()
        with ui.HStack(height=0):
            ui.Spacer(width=ui.Percent(10))
            ui.Button("Generate", height=40,  
                        clicked_fn=lambda: self._generate())
            ui.Spacer(width=ui.Percent(10))
        self.progress = ProgressBar()
        with ui.CollapsableFrame("ChatGPT Response / Log", height=0, collapsed=True):
            self.response_log = ui.Label("", word_wrap=True)

    def _build_combo_box(self):
        self.combo_model = ui.ComboBox(self.current_index, *[str(x) for x in self._areas] ).model
        def combo_changed(item_model, item):
            index_value_model = item_model.get_item_value_model(item)
            self.current_area = self._areas[index_value_model.as_int]
            self.current_index = index_value_model.as_int
            self.rebuild_frame()
        self._combo_changed_sub = self.combo_model.subscribe_item_changed_fn(combo_changed)

    def _create_new_area(self, area_name: str):
        if area_name == "":
            carb.log_warn("No area name provided")
            return
        new_area_name = CreateCubeFromCurve(self.get_prim_path(), area_name)
        self._areas.append(new_area_name)
        self.current_index = len(self._areas) - 1
        index_value_model = self.combo_model.get_item_value_model()
        index_value_model.set_value(self.current_index)
    
    def rebuild_frame(self):
        # we do want to update the area name and possibly last prompt?
        area_name = self.current_area.split("/World/Layout/")
        self._area_name_model.set_value(area_name[-1].replace("_", " "))
        attr_prompt = self.get_prim().GetAttribute('genai:prompt')
        if attr_prompt.IsValid():
            self._prompt_model.set_value(attr_prompt.Get())
        else:
            self._prompt_model.set_value("")
        self.frame.rebuild() 

    def _generate(self):
        prim = self.get_prim()
        attr = prim.GetAttribute('genai:prompt')
        if not attr.IsValid():
            attr = prim.CreateAttribute('genai:prompt', Sdf.ValueTypeNames.String)
        attr.Set(self.get_prompt())
        items_path = self.current_area + "/items"
        ctx = omni.usd.get_context()
        stage = ctx.get_stage()
        if stage.GetPrimAtPath(items_path).IsValid():
            omni.kit.commands.execute('DeletePrims',
                paths=[items_path],
                destructive=False)
        # asyncio.ensure_future(self.progress.fill_bar(0,100))
        run_loop = asyncio.get_event_loop()
        run_loop.create_task(call_Generate(self.get_prim_info(), 
                            self.get_prompt(), 
                            self._use_chatgpt.as_bool, 
                            self._use_deepsearch.as_bool,
                            self.response_log,
                            self.progress
                            ))

    # Returns a PrimInfo object containing the Length, Width, Origin and Area Name 
    def get_prim_info(self) -> PrimInfo:
        prim = self.get_prim()
        prim_info = None
        if prim.IsValid():
            prim_info = PrimInfo(prim, self.current_area)
        return prim_info
        
    # # Get the prim path specified
    def get_prim_path(self):
        ctx = omni.usd.get_context()
        selection = ctx.get_selection().get_selected_prim_paths()
        if len(selection) > 0:
            return str(selection[0])
        carb.log_warn("No Prim Selected")
        return ""
        
    # Get the area name specified
    def get_area_name(self):
        if self._area_name_model == "":
            carb.log_warn("No Area Name Provided")
        return self._area_name_model.as_string
        
    # Get the prompt specified
    def get_prompt(self):
        if self._prompt_model == "":
            carb.log_warn("No Prompt Provided")
        return self._prompt_model.as_string
    
    # Get the prim based on the Prim Path 
    def get_prim(self):
        ctx = omni.usd.get_context()
        stage = ctx.get_stage()
        prim = stage.GetPrimAtPath(self.current_area)
        if prim.IsValid() is None:
            carb.log_warn("No valid prim in the scene") 
        return prim

    def destroy(self):
        super().destroy()
        self._combo_changed_sub = None
        self._path_model = None
        self._prompt_model = None
        self._area_name_model = None
        self._use_deepsearch = None
        self._use_chatgpt = None