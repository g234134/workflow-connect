"""Support for simplified access to data on nodes of type lightspeed.trex.logic.Loop

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Wraps a number back into a range when it goes outside the boundaries.

Applies looping behavior to a value. Value is unchanged
if it is inside the range.
Component outputs Min Range if Min Range == Max Range and looping type is not None.
Inverted ranges
(max < min) are supported, but the results are undefined and may change without warning.
"""

from typing import Any
import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class LoopDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type lightspeed.trex.logic.Loop

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.loopingType
            inputs.maxRange
            inputs.minRange
            inputs.value
        Outputs:
            outputs.isReversing
            outputs.loopedValue

    Predefined Tokens:
        tokens.Clamp
        tokens.Loop
        tokens.NoLoop
        tokens.PingPong
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
        ('inputs:loopingType', 'token', 0, 'Looping Type', 'How the value should loop within the range.\nAllowed values:\n - Clamp: The value will be clamped to the range.\n  - Loop: The value will wrap around from max to min.\n  - NoLoop: The value will be unchanged.\n  - PingPong: The value will bounce back and forth between min and max.\n ', {ogn.MetadataKeys.ALLOWED_TOKENS: 'Clamp,Loop,NoLoop,PingPong', 'tokenCategory': 'Enum', ogn.MetadataKeys.ALLOWED_TOKENS_RAW: '["Clamp", "Loop", "NoLoop", "PingPong"]', ogn.MetadataKeys.DEFAULT: '"Loop"'}, True, "Loop", False, ''),
        ('inputs:maxRange', 'float,float[2],float[3],float[4]', 1, 'Max Range', 'The maximum value of the looping range.', {}, True, None, False, ''),
        ('inputs:minRange', 'float,float[2],float[3],float[4]', 1, 'Min Range', 'The minimum value of the looping range.', {}, True, None, False, ''),
        ('inputs:value', 'float,float[2],float[3],float[4]', 1, 'Value', 'The input value to apply looping to.', {}, True, None, False, ''),
        ('outputs:isReversing', 'bool', 0, 'Is Reversing', 'True if the value is in the reverse phase of ping pong looping. If passing `loopedValue` to a `Remap` component, hook this up to `shouldReverse` from that component.', {ogn.MetadataKeys.DEFAULT: 'false'}, True, False, False, ''),
        ('outputs:loopedValue', 'float,float[2],float[3],float[4]', 1, 'Looped Value', 'The value with looping applied.', {}, True, None, False, ''),
    ])

    class tokens:
        Clamp = "Clamp"
        Loop = "Loop"
        NoLoop = "NoLoop"
        PingPong = "PingPong"

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"loopingType", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = [self._attributes.loopingType]
            self._batchedReadValues = ["Loop"]

        @property
        def maxRange(self) -> og.RuntimeAttribute:
            """Get the runtime wrapper class for the attribute inputs.maxRange"""
            return og.RuntimeAttribute(self._attributes.maxRange.get_attribute_data(), self._context, True)

        @maxRange.setter
        def maxRange(self, value_to_set: Any):
            """Assign another attribute's value to outputs.maxRange"""
            if isinstance(value_to_set, og.RuntimeAttribute):
                self.maxRange.value = value_to_set.value
            else:
                self.maxRange.value = value_to_set

        @property
        def minRange(self) -> og.RuntimeAttribute:
            """Get the runtime wrapper class for the attribute inputs.minRange"""
            return og.RuntimeAttribute(self._attributes.minRange.get_attribute_data(), self._context, True)

        @minRange.setter
        def minRange(self, value_to_set: Any):
            """Assign another attribute's value to outputs.minRange"""
            if isinstance(value_to_set, og.RuntimeAttribute):
                self.minRange.value = value_to_set.value
            else:
                self.minRange.value = value_to_set

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
        def loopingType(self):
            return self._batchedReadValues[0]

        @loopingType.setter
        def loopingType(self, value):
            self._batchedReadValues[0] = value

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
        LOCAL_PROPERTY_NAMES = {"isReversing", "_batchedWriteValues"}
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedWriteValues = { }

        @property
        def loopedValue(self) -> og.RuntimeAttribute:
            """Get the runtime wrapper class for the attribute outputs.loopedValue"""
            return og.RuntimeAttribute(self._attributes.loopedValue.get_attribute_data(), self._context, False)

        @loopedValue.setter
        def loopedValue(self, value_to_set: Any):
            """Assign another attribute's value to outputs.loopedValue"""
            if isinstance(value_to_set, og.RuntimeAttribute):
                self.loopedValue.value = value_to_set.value
            else:
                self.loopedValue.value = value_to_set

        @property
        def isReversing(self):
            value = self._batchedWriteValues.get(self._attributes.isReversing)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.isReversing)
                return data_view.get()

        @isReversing.setter
        def isReversing(self, value):
            self._batchedWriteValues[self._attributes.isReversing] = value

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
        self.inputs = LoopDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = LoopDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = LoopDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'lightspeed.trex.logic.Loop'

        @staticmethod
        def compute(context, node):
            def database_valid():
                if db.inputs.maxRange.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute inputs:maxRange is not resolved, compute skipped')
                    return False
                if db.inputs.minRange.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute inputs:minRange is not resolved, compute skipped')
                    return False
                if db.inputs.value.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute inputs:value is not resolved, compute skipped')
                    return False
                if db.outputs.loopedValue.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute outputs:loopedValue is not resolved, compute skipped')
                    return False
                return True
            try:
                per_node_data = LoopDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = LoopDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = LoopDatabase(node)

            try:
                compute_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return LoopDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            LoopDatabase._initialize_per_node_data(node)
            initialize_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = LoopDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                LoopDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            LoopDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            LoopDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "lightspeed.trex.logic.ogn")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Loop")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "Transform")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Wraps a number back into a range when it goes outside the boundaries.\n\nApplies looping behavior to a value. Value is unchanged if it is inside the range.\nComponent outputs Min Range if Min Range == Max Range and looping type is not None.\nInverted ranges (max < min) are supported, but the results are undefined and may change without warning.")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                LoopDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(LoopDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        LoopDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(LoopDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("lightspeed.trex.logic.Loop")
