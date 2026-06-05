"""Support for simplified access to data on nodes of type lightspeed.trex.logic.Clamp

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Constrains a value to a specified range.

If the value is less than Min Value, returns Min Value. If the value is greater
than Max Value, returns Max Value. Otherwise, returns the value unchanged. Applies to each component of a vector individually.
"""

from typing import Any
import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class ClampDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type lightspeed.trex.logic.Clamp

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.maxValue
            inputs.minValue
            inputs.value
        Outputs:
            outputs.result
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
        ('inputs:maxValue', 'float', 0, 'Max Value', 'The maximum allowed value.', {ogn.MetadataKeys.DEFAULT: '1.0'}, True, 1.0, False, ''),
        ('inputs:minValue', 'float', 0, 'Min Value', 'The minimum allowed value.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
        ('inputs:value', 'float,float[2],float[3],float[4]', 1, 'Value', 'The value to clamp.', {}, True, None, False, ''),
        ('outputs:result', 'float,float[2],float[3],float[4]', 1, 'Result', 'The clamped value, constrained to [Min Value, Max Value].', {}, True, None, False, ''),
    ])

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"maxValue", "minValue", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = [self._attributes.maxValue, self._attributes.minValue]
            self._batchedReadValues = [1.0, 0.0]

        @property
        def value(self) -> og.RuntimeAttribute:
            """Get the runtime wrapper class for the attribute inputs.value"""
            return og.RuntimeAttribute(self._attributes.value.get_attribute_data(), self._context, True)

        @value.setter
        def value(self, value_to_set: Any):
            """Assign another attribute's value to outputs.value"""
            if isinstance(value_to_set, og.RuntimeAttribute):
                self.value.value = value_to_set.value
            else:
                self.value.value = value_to_set

        @property
        def maxValue(self):
            return self._batchedReadValues[0]

        @maxValue.setter
        def maxValue(self, value):
            self._batchedReadValues[0] = value

        @property
        def minValue(self):
            return self._batchedReadValues[1]

        @minValue.setter
        def minValue(self, value):
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
        LOCAL_PROPERTY_NAMES = { }
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedWriteValues = { }

        @property
        def result(self) -> og.RuntimeAttribute:
            """Get the runtime wrapper class for the attribute outputs.result"""
            return og.RuntimeAttribute(self._attributes.result.get_attribute_data(), self._context, False)

        @result.setter
        def result(self, value_to_set: Any):
            """Assign another attribute's value to outputs.result"""
            if isinstance(value_to_set, og.RuntimeAttribute):
                self.result.value = value_to_set.value
            else:
                self.result.value = value_to_set

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
        self.inputs = ClampDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = ClampDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = ClampDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'lightspeed.trex.logic.Clamp'

        @staticmethod
        def compute(context, node):
            def database_valid():
                if db.inputs.value.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute inputs:value is not resolved, compute skipped')
                    return False
                if db.outputs.result.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute outputs:result is not resolved, compute skipped')
                    return False
                return True
            try:
                per_node_data = ClampDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = ClampDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = ClampDatabase(node)

            try:
                compute_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return ClampDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            ClampDatabase._initialize_per_node_data(node)
            initialize_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = ClampDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                ClampDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            ClampDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            ClampDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "lightspeed.trex.logic.ogn")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Clamp")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "Transform")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Constrains a value to a specified range.\n\nIf the value is less than Min Value, returns Min Value. If the value is greater than Max Value, returns Max Value. Otherwise, returns the value unchanged. Applies to each component of a vector individually.")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                ClampDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(ClampDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        ClampDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(ClampDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("lightspeed.trex.logic.Clamp")
