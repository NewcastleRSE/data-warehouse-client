# Copyright 2020 Newcastle University.
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

# Python modules
import unittest

# Application modules
from data_warehouse_client import data_warehouse

# Test cases
class TestDataWarehouse(unittest.TestCase):
    """
    """
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.dw = None
        self.dw = data_warehouse.DataWarehouse("testdb-credentials.json","testdb")
        self.assertIsNotNone(self.dw)
        return super().setUp()
    
    def tearDown(self):
        return super().tearDown()
    
    def test_add_study(self):
        self.dw.add_study("Test Study")

    def test_add_trial(self):
        self.dw.add_study("Test Study 2")
        self.dw.add_trial(1, "Trial 1")
