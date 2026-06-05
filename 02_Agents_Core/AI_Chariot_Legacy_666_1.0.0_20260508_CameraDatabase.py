"""Support for simplified access to data on nodes of type lightspeed.trex.logic.Camera

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Provides information about the camera's position, direction, and field of view.

Outputs current camera properties including
position, orientation vectors, and projection parameters.

Uses free camera when both 'rtx.camera.useFreeCameraForComponents'
and free camera are enabled.
"""

import numpy
import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class CameraDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type lightspeed.trex.logic.Camera

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Outputs:
            outputs.aspectRatio
            outputs.farPlane
            outputs.forward
            outputs.fovDegrees
            outputs.fovRadians
            outputs.nearPlane
            outputs.position
            outputs.right
            outputs.up
    """

    # Imprint the generator and target ABI versions in the file for JIT generation
    GENERATOR_VERSION = (1, 79, 1)
    TARGET_VERSION = (2, 181, 8)

    # This is an internal object that provides per-class storage of a per-node data dictionary
    PER_NODE_DATA = {}

    # This is an internal object that describes unchanging attributes in a generic way
    # The values in this list are in no particular order, as a per-attribute tuple
    #     Name, Type, ExtendedTypeIndex, UiName, Description, Metadata,
    #     Is_Required, DefaultValue, Is_Deprecated, DeprecationMsg
    # You should not need to access any of this data directly, use the defined database interfaces
    INTERFACE = og.Database._get_interface([
        ('outputs:aspectRatio', 'float', 0, 'Aspect Ratio', "The camera's aspect ratio (width/height).", {ogn.MetadataKeys.DEFAULT: '1.0'}, True, 1.0, False, ''),
        ('outputs:farPlane', 'float', 0, 'Far Plane', "The camera's far clipping plane distance.", {ogn.MetadataKeys.DEFAULT: '1000.0'}, True, 1000.0, False, ''),
        ('outputs:forward', 'float3', 0, 'Forward', "The camera's normalized forward direction vector in world space.", {ogn.MetadataKeys.DEFAULT: '[0.0, 0.0, -1.0]'}, True, [0.0, 0.0, -1.0], False, ''),
        ('outputs:fovDegrees', 'float', 0, 'FOV (degrees)', 'The Y axis (vertical) Field of View of the camera in degrees. Note this value will always be positive.', {ogn.MetadataKeys.DEFAULT: '60.0'}, True, 60.0, False, ''),
        ('outputs:fovRadians', 'float', 0, 'FOV (radians)', 'The Y axis (vertical) Field of View of the camera in radians. Note this value will always be positive.', {ogn.MetadataKeys.DEFAULT: '1.047198'}, True, 1.047198, False, ''),
        ('outputs:nearPlane', 'float', 0, 'Near Plane', "The camera's near clipping plane distance.", {ogn.MetadataKeys.DEFAULT: '0.1'}, True, 0.1, False, ''),
        ('outputs:position', 'float3', 0, 'Position', 'The current camera position in world space.', {ogn.MetadataKeys.DEFAULT: '[0.0, 0.0, 0.0]'}, True, [0.0, 0.0, 0.0], False, ''),
        ('outputs:right', 'float3', 0, 'Right', "The camera's normalized right direction vector in world space.", {ogn.MetadataKeys.DEFAULT: '[1.0, 0.0, 0.0]'}, True, [1.0, 0.0, 0.0], False, ''),
        ('outputs:up', 'float3', 0, 'Up', "The camera's normalized up direction vector in world space.", {ogn.MetadataKeys.DEFAULT: '[0.0, 1.0, 0.0]'}, True, [0.0, 1.0, 0.0], False, ''),
    ])

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = { }
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = []
            self._batchedReadValues = []

        def _prefetch(self):
            readAttributes = self._batchedReadAttributes
            newValues = _og._prefetch_input_attributes_data(readAttributes)
            if len(readAttributes) == len(newValues):
                self._batchedReadValues = newValues

    class ValuesForOutputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"aspectRatio", "farPlane", "forward", "fovDegrees", "fovRadians", "nearPlane", "position", "right", "up", "_batchedWriteValues"}
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedWriteValues = { }

        @property
        def aspectRatio(self):
            value = self._batchedWriteValues.get(self._attributes.aspectRatio)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.aspectRatio)
                return data_view.get()

        @aspectRatio.setter
        def aspectRatio(self, value):
            self._batchedWriteValues[self._attributes.aspectRatio] = value

        @property
        def farPlane(self):
            value = self._batchedWriteValues.get(self._attributes.farPlane)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.farPlane)
                return data_view.get()

        @farPlane.setter
        def farPlane(self, value):
            self._batchedWriteValues[self._attributes.farPlane] = value

        @property
        def forward(self):
            value = self._batchedWriteValues.get(self._attributes.forward)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.forward)
                return data_view.get()

        @forward.setter
        def forward(self, value):
            self._batchedWriteValues[self._attributes.forward] = value

        @property
        def fovDegrees(self):
            value = self._batchedWriteValues.get(self._attributes.fovDegrees)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.fovDegrees)
                return data_view.get()

        @fovDegrees.setter
        def fovDegrees(self, value):
            self._batchedWriteValues[self._attributes.fovDegrees] = value

        @property
        def fovRadians(self):
            value = self._batchedWriteValues.get(self._attributes.fovRadians)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.fovRadians)
                return data_view.get()

        @fovRadians.setter
        def fovRadians(self, value):
            self._batchedWriteValues[self._attributes.fovRadians] = value

        @property
        def nearPlane(self):
            value = self._batchedWriteValues.get(self._attributes.nearPlane)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.nearPlane)
                return data_view.get()

        @nearPlane.setter
        def nearPlane(self, value):
            self._batchedWriteValues[self._attributes.nearPlane] = value

        @property
        def position(self):
            value = self._batchedWriteValues.get(self._attributes.position)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.position)
                return data_view.get()

        @position.setter
        def position(self, value):
            self._batchedWriteValues[self._attributes.position] = value

        @property
        def right(self):
            value = self._batchedWriteValues.get(self._attributes.right)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.right)
                return data_view.get()

        @right.setter
        def right(self, value):
            self._batchedWriteValues[self._attributes.right] = value

        @property
        def up(self):
            value = self._batchedWriteValues.get(self._attributes.up)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.up)
                return data_view.get()

        @up.setter
        def up(self, value):
            self._batchedWriteValues[self._attributes.up] = value

        def __getattr__(self, item: str):
            if item in self.LOCAL_PROPERTY_NAMES:
                return object.__getattribute__(self, item)
            else:
                return super().__getattr__(item)

        def __setattr__(self, item: str, new_value):
            if item in self.LOCAL_PROPERTY_NAMES:
                object.__setattr__(self, item, new_value)
            else:
                super().__setattr__(item, new_value)

        def _commit(self):
            _og._commit_output_attributes_data(self._batchedWriteValues)
            self._batchedWriteValues = { }

    class ValuesForState(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to state attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)

    def __init__(self, node):
        super().__init__(node)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT)
        self.inputs = CameraDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = CameraDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = CameraDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'lightspeed.trex.logic.Camera'

        @staticmethod
        def compute(context, node):
            def database_valid():
                return True
            try:
                per_node_data = CameraDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = CameraDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = CameraDatabase(node)

            try:
                compute_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return CameraDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            CameraDatabase._initialize_per_node_data(node)
            initialize_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = CameraDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                CameraDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            CameraDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            CameraDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "lightspeed.trex.logic.ogn")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Camera")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "Sense")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Provides information about the camera's position, direction, and field of view.\n\nOutputs current camera properties including position, orientation vectors, and projection parameters.\n\nUses free camera when both 'rtx.camera.useFreeCameraForComponents' and free camera are enabled.")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                CameraDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(CameraDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        CameraDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(CameraDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("lightspeed.trex.logic.Camera")
