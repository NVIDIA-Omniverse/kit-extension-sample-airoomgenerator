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

import sys
from pxr import Usd, Sdf, Gf
from .utils import scale_object_if_needed, apply_material_to_prim, create_prim, set_transformTRS_attrs

def place_deepsearch_results(gpt_results, query_result, root_prim_path, prim_info):
    index = 0
    
    max_x = sys.float_info.min
    max_y = sys.float_info.min

    index = 0
    #region determine scaling
    for item in query_result:
        next_object = gpt_results[index]
        index = index + 1

        # find the furthest object out in each direction        
        x_bound = next_object['X']
        y_bound = next_object['Z']

        if abs(x_bound) > max_x:
            max_x = abs(x_bound)
        
        if abs(y_bound) > max_y:
            max_y = abs(y_bound)

    # multiply by to (from 'radius' to diameter)
    max_x = max_x * 2
    max_y = max_y * 2

    # The factory is scaled up by 100....need to figure out how to get these global numbers...
    x_scale = (prim_info.length * 0.65) / max_x / 100
    y_scale = (prim_info.width * 0.65) / max_y / 100
    #endregion

    index = 0
    for item in query_result:
        item_name = item[0]
        item_paths = item[1]

        # Define Prim          
        prim_parent_path = root_prim_path + item_name.replace(" ", "_")
        prim_path = prim_parent_path + "/" + item_name.replace(" ", "_")

        parent_prim = create_prim(prim_parent_path)
            
        item_variant_sets = parent_prim.GetVariantSets()
        item_variant_set = item_variant_sets.GetVariantSet("Deepsearch")

        if not item_variant_set:
            item_variant_set = item_variant_sets.AddVariantSet("Deepsearch")

        # region start variants here        
        for item_path in item_paths:
            
            variant_count = len(item_variant_set.GetVariantNames())
            variant_index = variant_count + 1

            variant_name = "Version_" + "{:02d}".format(variant_index)
            item_variant_set.AddVariant(variant_name)
            
            item_variant_set.SetVariantSelection(variant_name)
            with item_variant_set.GetVariantEditContext():
                
                next_prim = create_prim(prim_path)
                # Add reference to USD Asset
                references: Usd.references = next_prim.GetReferences()
                
                # TODO: The query results should returnt he full path of the prim
                references.AddReference(
                    assetPath="omniverse://ov-simready" + item_path)

                # Add reference for future search refinement 
                config = next_prim.CreateAttribute("DeepSearch:Query", Sdf.ValueTypeNames.String)
                config.Set(item_name)

        item_variant_set.SetVariantSelection("Version_01")

        # endregion end variant here
                
        # HACK: All "GetAttribute" calls should need to check if the attribute exists
        # translate prim
        next_object = gpt_results[index]
        index = index + 1
        x = next_object['X'] * x_scale * 100
        y = next_object['Y'] * 1
        z = next_object['Z'] * y_scale * 100

        set_transformTRS_attrs(parent_prim, Gf.Vec3d(x, y, z), Gf.Vec3d(-90, 0, 0), Gf.Vec3d(1, 1, 1))
        scale_object_if_needed(prim_parent_path)

def place_greyboxes(gpt_results, root_prim_path):
    index = 0
    for item in gpt_results:
        # Define Prim
        prim_parent_path = root_prim_path + item['object_name'].replace(" ", "_")
        prim_path = prim_parent_path + "/" + item['object_name'].replace(" ", "_")

        # Define Dimensions and material
        length = item['Length'] 
        width = item['Width'] 
        height = item['Height'] 
        x = item['X'] 
        y = item['Z'] # shift bottom of object to y=0
        z = item['Y'] + height / 2
        material = item['Material']

        # Create Prim
        parent_prim = create_prim(prim_parent_path)
        set_transformTRS_attrs(parent_prim)
        prim = create_prim(prim_path, 'Cube')
        set_transformTRS_attrs(prim, translate=Gf.Vec3d(x, z, y), scale=Gf.Vec3d(length, width, height), rotate=Gf.Vec3d(-90, 0, 0))
        prim.GetAttribute('extent').Set([(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)])
        prim.GetAttribute('size').Set(1)

        index = index + 1

        # Add Attribute and Material
        attr = prim.CreateAttribute("object_name", Sdf.ValueTypeNames.String)
        attr.Set(item['object_name'])
        apply_material_to_prim(material, prim_path)
