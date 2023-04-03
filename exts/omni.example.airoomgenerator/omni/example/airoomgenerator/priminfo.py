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

from pxr import Usd, Gf

class PrimInfo:
    # Class that stores the prim info
    def __init__(self, prim: Usd.Prim, name: str = "") -> None:
        self.prim = prim
        self.child = prim.GetAllChildren()[0]
        self.length = self.GetLengthOfPrim()
        self.width = self.GetWidthOfPrim()
        self.origin = self.GetPrimOrigin()
        self.area_name = name

    def GetLengthOfPrim(self) -> str:
        # Returns the X value
        attr = self.child.GetAttribute('xformOp:scale')
        x_scale = attr.Get()[0]
        return  str(x_scale)

    def GetWidthOfPrim(self) -> str:
        # Returns the Z value
        attr = self.child.GetAttribute('xformOp:scale')
        z_scale = attr.Get()[2]
        return str(z_scale)

    def GetPrimOrigin(self) -> str:
        attr = self.prim.GetAttribute('xformOp:translate')
        origin = Gf.Vec3d(0,0,0)
        if attr: 
            origin = attr.Get()
        phrase = str(origin[0]) + ", " + str(origin[1]) + ", " + str(origin[2]) 
        return phrase