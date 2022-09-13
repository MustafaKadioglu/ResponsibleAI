# Copyright 2022 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0


from RAI.metrics.metric_group import MetricGroup
import scipy.stats
from RAI.utils.utils import calculate_per_mapped_features
import os


class CorrelationStatRegressionSlow(MetricGroup, class_location=os.path.abspath(__file__)):
    def __init__(self, ai_system) -> None:
        super().__init__(ai_system)
        
    def update(self, data):
        pass

    def compute(self, data_dict):
        args = {}
        if self.ai_system.metric_manager.user_config is not None and "stats" in self.ai_system.metric_manager.user_config and "args" in self.ai_system.metric_manager.user_config["stats"]:
            args = self.ai_system.metric_manager.user_config["stats"]["args"]
        data = data_dict["data"]
        scalar_data = data.scalar
        map = self.ai_system.meta_database.scalar_map
        features = self.ai_system.meta_database.features

        self.metrics["siegel_slopes"].value = calculate_per_mapped_features(scipy.stats.siegelslopes, map, features, scalar_data, data.y)
        self.metrics["theil_slopes"].value = calculate_per_mapped_features(scipy.stats.theilslopes, map, features, scalar_data, data.y)
