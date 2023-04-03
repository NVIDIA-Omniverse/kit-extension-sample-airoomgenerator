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

import omni.kit.commands
from pxr import  Gf, Sdf, UsdGeom
from .materials import *
import carb

def CreateCubeFromCurve(curve_path: str, area_name: str = ""):
    ctx = omni.usd.get_context()
    stage = ctx.get_stage()
    min_coords, max_coords = get_coords_from_bbox(curve_path)
    x,y,z = get_bounding_box_dimensions(curve_path)
    xForm_scale = Gf.Vec3d(x, 1, z)
    cube_scale = Gf.Vec3d(0.01, 0.01, 0.01)
    prim = stage.GetPrimAtPath(curve_path)
    origin = prim.GetAttribute('xformOp:translate').Get()
    if prim.GetTypeName() == "BasisCurves":
        origin = Gf.Vec3d(min_coords[0]+x/2, 0, min_coords[2]+z/2)

    area_path = '/World/Layout/Area'
    if len(area_name) != 0:
        area_path = '/World/Layout/' + area_name.replace(" ", "_")

    new_area_path = omni.usd.get_stage_next_free_path(stage, area_path, False)
    new_cube_xForm_path = new_area_path + "/" + "Floor"
    new_cube_path = new_cube_xForm_path + "/" + "Cube"

    # Create xForm to hold all items
    item_container = create_prim(new_area_path)
    set_transformTRS_attrs(item_container, translate=origin)

    # Create Scale Xform for floor
    xform = create_prim(new_cube_xForm_path)
    set_transformTRS_attrs(xform, scale=xForm_scale)

    # Create Floor Cube
    omni.kit.commands.execute('CreateMeshPrimWithDefaultXform',
        prim_type='Cube',
        prim_path=new_cube_path,
        select_new_prim=True
        )
    cube = stage.GetPrimAtPath(new_cube_path)
    set_transformTRS_attrs(cube, scale=cube_scale)
    cube.CreateAttribute("primvar:area_name", Sdf.ValueTypeNames.String, custom=True).Set(area_name)

    omni.kit.commands.execute('DeletePrims',
        paths=[curve_path],
        destructive=False)    

    apply_material_to_prim('Concrete_Rough_Dirty', new_area_path)
    return new_area_path

def apply_material_to_prim(material_name: str, prim_path: str):
    ctx = omni.usd.get_context()
    stage = ctx.get_stage()
    looks_path = '/World/Looks/'
    mat_path = looks_path + material_name
    mat_prim = stage.GetPrimAtPath(mat_path)
    if MaterialPresets.get(material_name, None) is not None:
        if not mat_prim.IsValid():
            omni.kit.commands.execute('CreateMdlMaterialPrimCommand',
                mtl_url=MaterialPresets[material_name],
                mtl_name=material_name,
                mtl_path=mat_path)
        omni.kit.commands.execute('BindMaterialCommand',
            prim_path=prim_path,
            material_path=mat_path)
    
def create_prim(prim_path, prim_type='Xform'):
    ctx = omni.usd.get_context()
    stage = ctx.get_stage()
    prim = stage.DefinePrim(prim_path)
    if prim_type == 'Xform':
        xform = UsdGeom.Xform.Define(stage, prim_path)
    else:
        xform = UsdGeom.Cube.Define(stage, prim_path)
    create_transformOps_for_xform(xform)
    return prim

def create_transformOps_for_xform(xform):
    xform.AddTranslateOp()
    xform.AddRotateXYZOp()
    xform.AddScaleOp()

def set_transformTRS_attrs(prim, translate: Gf.Vec3d = Gf.Vec3d(0,0,0), rotate: Gf.Vec3d=Gf.Vec3d(0,0,0), scale: Gf.Vec3d=Gf.Vec3d(1,1,1)):
    prim.GetAttribute('xformOp:translate').Set(translate)
    prim.GetAttribute('xformOp:rotateXYZ').Set(rotate)
    prim.GetAttribute('xformOp:scale').Set(scale)
    
def get_bounding_box_dimensions(prim_path: str):
    min_coords, max_coords = get_coords_from_bbox(prim_path)
    length = max_coords[0] - min_coords[0]
    width = max_coords[1] - min_coords[1]
    height = max_coords[2] - min_coords[2]
    return length, width, height

def get_coords_from_bbox(prim_path: str):
    ctx = omni.usd.get_context()
    bbox = ctx.compute_path_world_bounding_box(prim_path)
    min_coords, max_coords = bbox
    return min_coords, max_coords

def scale_object_if_needed(prim_path):
    stage = omni.usd.get_context().get_stage()

    length, width, height = get_bounding_box_dimensions(prim_path)
    largest_dimension = max(length, width, height)

    if largest_dimension < 10:
        prim = stage.GetPrimAtPath(prim_path)

        # HACK: All Get Attribute Calls need to check if the attribute exists and add it if it doesn't
        if prim.IsValid():
            scale_attr = prim.GetAttribute('xformOp:scale')
            if scale_attr.IsValid():
                current_scale = scale_attr.Get()
                new_scale = (current_scale[0] * 100, current_scale[1] * 100, current_scale[2] * 100)
                scale_attr.Set(new_scale)
                carb.log_info(f"Scaled object by 100 times: {prim_path}")
            else:
                carb.log_info(f"Scale attribute not found for prim at path: {prim_path}")
        else:
            carb.log_info(f"Invalid prim at path: {prim_path}")
    else:
        carb.log_info(f"No scaling needed for object: {prim_path}")