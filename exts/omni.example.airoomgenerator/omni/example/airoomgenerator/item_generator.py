# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#hotkey
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pxr import Usd, Sdf, Gf
from .utils import scale_object_if_needed, apply_material_to_prim, create_prim, set_transformTRS_attrs

def place_deepsearch_results(gpt_results, query_result, root_prim_path):
    index = 0
    for item in query_result:
        item_name = item[0]
        item_path = item[1]
        # Define Prim          
        prim_parent_path = root_prim_path + item_name.replace(" ", "_")
        prim_path = prim_parent_path + "/" + item_name.replace(" ", "_")

        parent_prim = create_prim(prim_parent_path)
        next_prim = create_prim(prim_path)

        # Add reference to USD Asset
        references: Usd.references = next_prim.GetReferences()
        
        # TODO: The query results should returnt he full path of the prim
        references.AddReference(
            assetPath="omniverse://ov-simready" + item_path)

        # Add reference for future search refinement 
        config = next_prim.CreateAttribute("DeepSearch:Query", Sdf.ValueTypeNames.String)
        config.Set(item_name)
        
        # HACK: All "GetAttribute" calls should need to check if the attribute exists
        # translate prim
        next_object = gpt_results[index]
        index = index + 1
        x = next_object['X']
        y = next_object['Y']
        z = next_object['Z']

        set_transformTRS_attrs(parent_prim, Gf.Vec3d(x,y,z), Gf.Vec3d(0,-90,-90), Gf.Vec3d(1.0,1.0,1.0))
        scale_object_if_needed(prim_parent_path)

def place_greyboxes(gpt_results, root_prim_path):
    index = 0
    for item in gpt_results:
        # Define Prim          
        prim_parent_path = root_prim_path + item['object_name'].replace(" ", "_")
        prim_path = prim_parent_path + "/" + item['object_name'].replace(" ", "_")

        # Define Dimensions and material
        length = item['Length']/100
        width = item['Width']/100
        height = item['Height']/100
        x = item['X']
        y = item['Y']+height*100*.5 #shift bottom of object to y=0
        z = item['Z']
        material = item['Material']

        # Create Prim
        parent_prim = create_prim(prim_parent_path)
        set_transformTRS_attrs(parent_prim)
        prim = create_prim(prim_path, 'Cube')
        set_transformTRS_attrs(prim, translate=Gf.Vec3d(x,y,z), scale=Gf.Vec3d(length, height, width))
        prim.GetAttribute('extent').Set([(-50.0, -50.0, -50.0), (50.0, 50.0, 50.0)])
        prim.GetAttribute('size').Set(100)

        index = index + 1

        # Add Attribute and Material
        attr = prim.CreateAttribute("object_name", Sdf.ValueTypeNames.String)
        attr.Set(item['object_name'])
        apply_material_to_prim(material, prim_path)



