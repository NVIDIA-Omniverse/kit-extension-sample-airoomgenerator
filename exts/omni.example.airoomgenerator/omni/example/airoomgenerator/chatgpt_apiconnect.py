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

import json
import omni.usd
import carb
import os
import aiohttp
import asyncio
from pxr import Sdf
from .prompts import system_input, user_input, assistant_input
from .deep_search import query_items
from .item_generator import place_greyboxes, place_deepsearch_results

from .results_office import ds_office_1, ds_office_2, ds_office_3, gpt_office_1

async def chatGPT_call(prompt: str):
    # Load your API key from an environment variable or secret management service
    settings = carb.settings.get_settings()
    
    apikey = settings.get_as_string("/persistent/exts/omni.example.airoomgenerator/APIKey")
    my_prompt = prompt.replace("\n", " ")
    
    # Send a request API
    try:
        parameters = {
            "model": "gpt-3.5-turbo",
            "messages": [
                    {"role": "system", "content": system_input},
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": assistant_input},
                    {"role": "user", "content": my_prompt}
                ]
        }
        chatgpt_url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": "Bearer %s" % apikey}
        # Create a completion using the chatGPT model
        async with aiohttp.ClientSession() as session:
            async with session.post(chatgpt_url, headers=headers, json=parameters) as r:
                response = await r.json()
        text = response["choices"][0]["message"]['content']
    except Exception as e:
        carb.log_error("An error as occurred")
        return None, str(e)

    # Parse data that was given from API
    try: 
        #convert string to  object
        data = json.loads(text)
    except ValueError as e:
        carb.log_error(f"Exception occurred: {e}")
        return None, text
    else: 
        # Get area_objects_list
        object_list = data['area_objects_list']
        
        return object_list, text

async def call_Generate(prim_info, prompt, use_gpt, use_deepsearch, progress_widget, target, agent_task_path):
    
    try:
        run_loop = asyncio.get_event_loop()
        progress_widget.show_bar(True)
        progress_bar_task = run_loop.create_task(progress_widget.play_anim_forever())
        response = ""
        #chain the prompt
        area_name = prim_info.area_name
        concat_prompt = area_name[-1].replace("_", " ") + ", " + str(prim_info.length) + "x" + str(prim_info.width) + ", origin at (0.0, 0.0, 0.0), generate a list of appropriate items in the correct places. " + prompt

        if use_gpt:          #when calling the API
            objects, response = await chatGPT_call(concat_prompt)
        else:                       #when testing and you want to skip the API call
            data = json.loads(gpt_office_1)
            objects = data['area_objects_list']
        if objects is None:
            return

        agent_name = "kit"

        # region Check if agent sub-layer exists else create
        stage = omni.usd.get_context().get_stage()
        root_layer: Sdf.Layer = stage.GetRootLayer()
        root_directory = os.path.dirname(root_layer.realPath)

        sub_layers = root_layer.subLayerPaths
        sub_layer_path = root_directory + "/" + agent_name + ".usd"

        # This looks for the agent sub_layer in the stage (not on the nucleus server)
        # TODO: Make this relative path more flexible
        sub_layer = None
        for layer in sub_layers:
            if layer == sub_layer_path or layer == "./" + agent_name + ".usd":
                sub_layer = Sdf.Layer.Find(sub_layer_path)
                break

        #This assumes that if the agent sub_layer is not in the stage it does not exist on Nucleus
        # HACK: This will fail if the layer with this name exists on nucleus next to the root scene
        if not sub_layer:
            sub_layer = Sdf.Layer.CreateNew(sub_layer_path)
            root_layer.subLayerPaths.append(sub_layer.identifier)
        # endregion

        # set the agent layer as the edit target
        stage.SetEditTarget(sub_layer)

        target_variant_sets = target.GetVariantSets()
        color_variant_set = target_variant_sets.GetVariantSet("Kit")

        if not color_variant_set:
            color_variant_set = target_variant_sets.AddVariantSet("Kit")

        variant_count = len(color_variant_set.GetVariantNames())
        variant_index = variant_count + 1

        root_prim_path = target.GetPath().pathString + "/AIResults_" + "{:02d}".format(variant_index) + "/"
        
        # HACK: Hard-coded leading zeros, should look at how many variant are there
        #       and then rename existing variants if necessary to add 0s as needed
        variant_name = "Version_" + "{:02d}".format(variant_index)
        color_variant_set.AddVariant(variant_name)
        color_variant_set.SetVariantSelection(variant_name)

        # With VariantContext
        with color_variant_set.GetVariantEditContext():
            if use_deepsearch:
                settings = carb.settings.get_settings()
                nucleus_path = settings.get_as_string("/persistent/exts/omni.example.airoomgenerator/deepsearch_nucleus_path")
                if nucleus_path == "" or nucleus_path == "(ENTERPRISE ONLY) Enter Nucleus Path Here":
                    nucleus_path = "omniverse://ov-simready/"

                filter_path = settings.get_as_string("/persistent/exts/omni.example.airoomgenerator/filter_path")
                filter_paths = filter_path.split(',')

                if len(filter_paths) == 0 or (len(filter_paths) == 1 and filter_paths[0] == ""):       
                    filter_paths = ["/Projects/simready_content/common_assets/props/",
                                    "/Projects/simready_content/common_assets/vehicle/toyota/forklift/",
                                    "/Projects/simready_content/common_assets/props_vegetation/"]

                queries = list()
                for item in objects:
                    queries.append(item['object_name'])

                query_result = await query_items(queries=queries, url=nucleus_path, paths=filter_paths)
                
                # query_result = json.loads(ds_office_1)

                if query_result is not None and len(query_result) > 0:
                    carb.log_info("placing deepsearch results")
                    place_deepsearch_results(
                        gpt_results=objects,
                        query_result=query_result,
                        root_prim_path=root_prim_path,
                        prim_info=prim_info)
                else:
                    place_greyboxes(                    
                        gpt_results=objects,
                        root_prim_path=root_prim_path)
                carb.log_info("results placed")
            else:
                place_greyboxes(                    
                    gpt_results=objects,
                    root_prim_path=root_prim_path)

        # Change the layer edit target back to the root layer
        stage.SetEditTarget(root_layer)
    except:
        carb.log_error("gpt or deepsearch failed")
    finally:
        progress_bar_task.cancel
        await asyncio.sleep(1)
        progress_widget.show_bar(False)
