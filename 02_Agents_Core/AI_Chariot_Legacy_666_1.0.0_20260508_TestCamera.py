import os
import omni.kit.test
import omni.graph.core as og
import omni.graph.core.tests as ogts
from omni.graph.core.tests.omnigraph_test_utils import _TestGraphAndNode
from omni.graph.core.tests.omnigraph_test_utils import _test_clear_scene
from omni.graph.core.tests.omnigraph_test_utils import _test_setup_scene
from omni.graph.core.tests.omnigraph_test_utils import _test_verify_scene


class TestOgn(ogts.OmniGraphTestCase):

    async def test_data_access(self):
        from lightspeed.trex.logic.ogn.ogn.CameraDatabase import CameraDatabase
        test_file_name = "CameraTemplate.usda"
        usd_path = os.path.join(os.path.dirname(__file__), "usd", test_file_name)
        if not os.path.exists(usd_path):  # pragma: no cover
            self.assertTrue(False, f"{usd_path} not found for loading test")
        (result, error) = await ogts.load_test_file(usd_path)
        self.assertTrue(result, f'{error} on {usd_path}')
        test_node = og.Controller.node("/TestGraph/Template_lightspeed_trex_logic_Camera")
        database = CameraDatabase(test_node)
        self.assertTrue(test_node.is_valid())
        node_type_name = test_node.get_type_name()
        self.assertEqual(og.GraphRegistry().get_node_type_version(node_type_name), 1)

        def _attr_error(attribute: og.Attribute, usd_test: bool) -> str:  # pragma no cover
            test_type = "USD Load" if usd_test else "Database Access"
            return f"{node_type_name} {test_type} Test - {attribute.get_name()} value error"


        self.assertTrue(test_node.get_attribute_exists("outputs:aspectRatio"))
        attribute = test_node.get_attribute("outputs:aspectRatio")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.aspectRatio
        database.outputs.aspectRatio = db_value

        self.assertTrue(test_node.get_attribute_exists("outputs:farPlane"))
        attribute = test_node.get_attribute("outputs:farPlane")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.farPlane
        database.outputs.farPlane = db_value

        self.assertTrue(test_node.get_attribute_exists("outputs:forward"))
        attribute = test_node.get_attribute("outputs:forward")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.forward
        database.outputs.forward = db_value

        self.assertTrue(test_node.get_attribute_exists("outputs:fovDegrees"))
        attribute = test_node.get_attribute("outputs:fovDegrees")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.fovDegrees
        database.outputs.fovDegrees = db_value

        self.assertTrue(test_node.get_attribute_exists("outputs:fovRadians"))
        attribute = test_node.get_attribute("outputs:fovRadians")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.fovRadians
        database.outputs.fovRadians = db_value

        self.assertTrue(test_node.get_attribute_exists("outputs:nearPlane"))
        attribute = test_node.get_attribute("outputs:nearPlane")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.nearPlane
        database.outputs.nearPlane = db_value

        self.assertTrue(test_node.get_attribute_exists("outputs:position"))
        attribute = test_node.get_attribute("outputs:position")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.position
        database.outputs.position = db_value

        self.assertTrue(test_node.get_attribute_exists("outputs:right"))
        attribute = test_node.get_attribute("outputs:right")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.right
        database.outputs.right = db_value

        self.assertTrue(test_node.get_attribute_exists("outputs:up"))
        attribute = test_node.get_attribute("outputs:up")
        self.assertTrue(attribute.is_valid())
        db_value = database.outputs.up
        database.outputs.up = db_value
        temp_setting = database.inputs._setting_locked
        database.outputs._testing_sample_value = True
        database.inputs._setting_locked = temp_setting
        self.assertTrue(database.outputs._testing_sample_value)
