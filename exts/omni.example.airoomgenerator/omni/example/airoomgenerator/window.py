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
    progress = None
    use_deepsearch = None
    use_chatgpt = None

    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(title, **kwargs)
        
        # Models
        self._path_model = ui.SimpleStringModel()
        self._prompt_model = ui.SimpleStringModel("generate warehouse objects")
        GenAIWindow.use_deepsearch = ui.SimpleBoolModel(True)
        GenAIWindow.use_chatgpt = ui.SimpleBoolModel(True)
        self.response_log = None
        self.current_index = -1
        self.current_area = None
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
                        ui.Label("Area Path", width=ui.Percent(30))
                        ui.StringField(model=self._path_model)
                        ui.Button(name="create", width=30, height=30, clicked_fn=lambda: self._get_area_path())
                    ui.Line()
                    with ui.HStack(height=ui.Percent(50)):
                        ui.Label("Prompt", width=0)
                        ui.StringField(model=self._prompt_model, multiline=True)
                    ui.Line()
                    with ui.HStack(height=0):
                        ui.Spacer()
                        ui.Label("Use ChatGPT: ")
                        ui.CheckBox(model=GenAIWindow.use_chatgpt)
                        ui.Label("Use Deepsearch: ", tooltip="ENTERPRISE USERS ONLY")
                        ui.CheckBox(model=GenAIWindow.use_deepsearch)
                        ui.Spacer()
                    with ui.HStack(height=0):
                        ui.Spacer(width=ui.Percent(10))
                        ui.Button("Generate", height=40,  
                                    clicked_fn=lambda: self._generate())
                        ui.Spacer(width=ui.Percent(10))
                    GenAIWindow.progress = ProgressBar()
                    with ui.CollapsableFrame("ChatGPT Response / Log", height=0, collapsed=True):
                        self.response_log = ui.Label("", word_wrap=True)
    
    def _save_settings(self, dialog):
        values = dialog.get_values()

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
    
    def rebuild_frame(self):
        # we do want to update the area name and possibly last prompt?
        attr_prompt = self.get_prim().GetAttribute('genai:prompt')
        if attr_prompt.IsValid():
            self._prompt_model.set_value(attr_prompt.Get())
        else:
            self._prompt_model.set_value("")
        self.frame.rebuild() 

    def _generate(self):
        target = self.get_prim()         
         
        attr = target.GetAttribute('genai:prompt')
        if not attr.IsValid():
            attr = target.CreateAttribute('genai:prompt', Sdf.ValueTypeNames.String)
        attr.Set(self.get_prompt())

        run_loop = asyncio.get_event_loop()
        run_loop.create_task(call_Generate(
                            get_prim_info(target, target.GetName()),
                            self.get_prompt(),
                            GenAIWindow.use_chatgpt.as_bool,  # use chatGPT
                            GenAIWindow.use_deepsearch.as_bool,  # use DeepSearch
                            GenAIWindow.progress,
                            target,
                            agent_task_path=""))
        
    # # Get the selected area path
    def _get_area_path(self):
        self._path_model.set_value(self.get_prim_path())

    # # Get the prim path specified
    def get_prim_path(self):
        ctx = omni.usd.get_context()
        selection = ctx.get_selection().get_selected_prim_paths()
        if len(selection) > 0:
            return str(selection[0])
        carb.log_warn("No Prim Selected")
        return ""
        
    # Get the prompt specified
    def get_prompt(self):
        if self._prompt_model == "":
            carb.log_warn("No Prompt Provided")
        return self._prompt_model.as_string
    
    # Get the prim based on the Prim Path 
    def get_prim(self):
        ctx = omni.usd.get_context()
        stage = ctx.get_stage()
        prim = stage.GetPrimAtPath(self._path_model.as_string)
        if prim.IsValid() is None:
            carb.log_warn("No valid prim in the scene") 
        return prim

    def destroy(self):
        super().destroy()
        self._path_model = None
        self._prompt_model = None
        self._use_deepsearch = None
        self._use_chatgpt = None

# Returns a PrimInfo object containing the Length, Width, Origin and Area Name
def get_prim_info(prim, area_name: str) -> PrimInfo:
    prim_info = None
    if prim.IsValid():
        prim_info = PrimInfo(prim, area_name)
    return prim_info
