"""Support for simplified access to data on nodes of type lightspeed.trex.logic.AngleToMesh

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Measures the angle between a ray and a mesh's center point.  This can be used to determine if the camera is looking at a
mesh.

Calculates the angle between a ray (from position + direction) and the direction to a mesh's transformed centroid.
"""

import numpy
import sys
import traceback
import usdrt

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class AngleToMeshDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type lightspeed.trex.logic.AngleToMesh

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.direction
            inputs.target
            inputs.worldPosition
        Outputs:
            outputs.angleDegrees
            outputs.angleRadians
            outputs.directionToCentroid
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
        ('inputs:direction', 'float3', 0, 'Direction', 'The direction vector of the ray (does not need to be normalized).', {ogn.MetadataKeys.DEFAULT: '[0.0, 0.0, 1.0]'}, True, [0.0, 0.0, 1.0], False, ''),
        ('inputs:target', 'target', 0, 'Target', 'The mesh prim to get the centroid from. Must be a mesh prim.', {'filterPrimTypes': 'UsdGeomMesh'}, True, None, False, ''),
        ('inputs:worldPosition', 'float3', 0, 'World Position', 'The world space position to use as the origin of the ray.', {ogn.MetadataKeys.DEFAULT: '[0.0, 0.0, 0.0]'}, True, [0.0, 0.0, 0.0], False, ''),
        ('outputs:angleDegrees', 'float', 0, 'Angle (Degrees)', 'The angle in degrees between the ray direction and the direction to the mesh centroid.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
        ('outputs:angleRadians', 'float', 0, 'Angle (Radians)', 'The angle in radians between the ray direction and the direction to the mesh centroid.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
        ('outputs:directionToCentroid', 'float3', 0, 'Direction to Centroid', 'The normalized direction vector from the world position to the mesh centroid.', {ogn.MetadataKeys.DEFAULT: '[0.0, 0.0, 0.0]'}, True, [0.0, 0.0, 0.0], False, ''),
    ])

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.target = og.AttributeRole.TARGET
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"direction", "worldPosition", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = [self._attributes.direction, self._attributes.worldPosition]
            self._batchedReadValues = [[0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]

        @property
        def target(self):
            data_view = og.AttributeValueHelper(self._attributes.target)
            return data_view.get()

        @target.setter
        def target(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.target)
            data_view = og.AttributeValueHelper(self._attributes.target)
            data_view.set(value)
            self.target_size = data_view.get_array_size()

        @property
        def direction(self):
            return self._batchedReadValues[0]

        @direction.setter
        def direction(self, value):
            self._batchedReadValues[0] = value

        @property
        def worldPosition(self):
            return self._batchedReadValues[1]

        @worldPosition.setter
        def worldPosition(self, value):
            self._batchedReadValues[1] = value

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

        def _prefetch(self):
            readAttributes = self._batchedReadAttributes
            newValues = _og._prefetch_input_attributes_data(readAttributes)
            if len(readAttributes) == len(newValues):
                self._batchedReadValues = newValues

    class ValuesForOutputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"angleDegrees", "angleRadians", "directionToCentroid", "_batchedWriteValues"}
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedWriteValues = { }

        @property
        def angleDegrees(self):
            value = self._batchedWriteValues.get(self._attributes.angleDegrees)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.angleDegrees)
                return data_view.get()

        @angleDegrees.setter
        def angleDegrees(self, value):
            self._batchedWriteValues[self._attributes.angleDegrees] = value

        @property
        def angleRadians(self):
            value = self._batchedWriteValues.get(self._attributes.angleRadians)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.angleRadians)
                return data_view.get()

        @angleRadians.setter
        def angleRadians(self, value):
            self._batchedWriteValues[self._attributes.angleRadians] = value

        @property
        def directionToCentroid(self):
            value = self._batchedWriteValues.get(self._attributes.directionToCentroid)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.directionToCentroid)
                return data_view.get()

        @directionToCentroid.setter
        def directionToCentroid(self, value):
            self._batchedWriteValues[self._attributes.directionToCentroid] = value

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
        self.inputs = AngleToMeshDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = AngleToMeshDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = AngleToMeshDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'lightspeed.trex.logic.AngleToMesh'

        @staticmethod
        def compute(context, node):
            def database_valid():
                return True
            try:
                per_node_data = AngleToMeshDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = AngleToMeshDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = AngleToMeshDatabase(node)

            try:
                compute_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return AngleToMeshDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            AngleToMeshDatabase._initialize_per_node_data(node)
            initialize_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = AngleToMeshDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                AngleToMeshDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            AngleToMeshDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            AngleToMeshDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "lightspeed.trex.logic.ogn")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Angle to Mesh")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "Sense")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Measures the angle between a ray and a mesh's center point.  This can be used to determine if the camera is looking at a mesh.\n\nCalculates the angle between a ray (from position + direction) and the direction to a mesh's transformed centroid.")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                AngleToMeshDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(AngleToMeshDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        AngleToMeshDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(AngleToMeshDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("lightspeed.trex.logic.AngleToMesh")
