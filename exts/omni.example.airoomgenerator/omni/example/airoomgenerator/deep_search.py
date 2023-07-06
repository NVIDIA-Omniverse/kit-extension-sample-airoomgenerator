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

from omni.kit.ngsearch.client import NGSearchClient
import asyncio
import carb

async def query_items(queries, url: str, paths):

    result = list(tuple())        
    for query in queries:
        query_result = await _query_first(query, url, paths)

        if query_result is not None:
            result.append(query_result)
        
    return result

async def _query_first(query: str, url: str, paths):

    filtered_query = "ext:usd,usdz,usda "

    if len(paths) > 0:
        filtered_query = filtered_query + " path: "

        for path in paths:
            filtered_query = filtered_query + "\"" + str(path) + "\","
        
        filtered_query = filtered_query[:-1]
    
        filtered_query = filtered_query + " "

    filtered_query = filtered_query + query

    search_result = await NGSearchClient.get_instance().find2(
        query=filtered_query, url=url)
    
    if search_result is not None:
        if len(search_result.paths) > 0:
            return (query, search_result.paths[0].uri)
    else:
        carb.log_warn(f"Search Results came up with nothing for {query}. Make sure you've configured your nucleus path")
    return None
    
async def query_all(query: str, url: str, paths):

    filtered_query = "ext:usd,usdz,usda " + query
    return await NGSearchClient.get_instance().find2(query=filtered_query, url=url)
        
