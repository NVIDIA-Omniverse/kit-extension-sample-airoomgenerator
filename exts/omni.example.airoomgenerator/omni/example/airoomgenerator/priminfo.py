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

from pxr import Usd, UsdGeom, Gf

class PrimInfo:
    # Class that stores the prim info
    def __init__(self, prim: Usd.Prim, name: str = "") -> None:
        self.prim = prim
        self.child = prim.GetAllChildren()[0]
        self.bbox: Gf.Range3d = self.compute_bbox()
        self.length = self.GetLengthOfPrim()
        self.width = self.GetWidthOfPrim()
        self.origin = self.GetPrimOrigin()
        self.area_name = name

    def compute_bbox(self) -> Gf.Range3d:
        """
        https://docs.omniverse.nvidia.com/prod_kit/prod_kit/programmer_ref/usd/transforms/compute-prim-bounding-box.html
        """
        imageable = UsdGeom.Imageable(self.prim)
        time = Usd.TimeCode.Default()  # The time at which we compute the bounding box
        bound = imageable.ComputeWorldBound(time, UsdGeom.Tokens.default_)
        bound_range = bound.ComputeAlignedBox()
        return bound_range
    
    def GetLengthOfPrim(self):
        return self.bbox.max[0] - self.bbox.min[0]
    
    def GetWidthOfPrim(self):
        return self.bbox.max[2] - self.bbox.min[2]

    def GetPrimOrigin(self) -> str:
        attr = self.prim.GetAttribute('xformOp:translate')
        origin = Gf.Vec3d(0,0,0)
        if attr: 
            origin = attr.Get()
        phrase = str(origin[0]) + ", " + str(origin[1]) + ", " + str(origin[2]) 
        return phrase