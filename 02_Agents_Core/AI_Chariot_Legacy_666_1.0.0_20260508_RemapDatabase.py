"""Support for simplified access to data on nodes of type lightspeed.trex.logic.Remap

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Smoothly maps a value from one range to another range with customizable easing curves.

Remaps a value from an input range
to an output range with optional easing. Values will be normalized (mapped from input range to 0-1), eased (changed from
linear to some curve), then mapped (0-1 value to output range).

Note: Input values outside of input range are valid, and
easing can lead to the output value being outside of the output range even when input is inside the input range.

Inverted
ranges (max < min) are supported.
"""

from typing import Any
import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class RemapDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type lightspeed.trex.logic.Remap

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.clampInput
            inputs.easingType
            inputs.inputMax
            inputs.inputMin
            inputs.outputMax
            inputs.outputMin
            inputs.shouldReverse
            inputs.value
        Outputs:
            outputs.output

    Predefined Tokens:
        tokens.Bounce
        tokens.Cubic
        tokens.EaseIn
        tokens.EaseInOut
        tokens.EaseOut
        tokens.Elastic
        tokens.Exponential
        tokens.Linear
        tokens.Sine
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
        ('inputs:clampInput', 'bool', 0, 'Clamp Input', 'If true, `value` will be clamped to the input range.', {ogn.MetadataKeys.DEFAULT: 'false'}, False, False, False, ''),
        ('inputs:easingType', 'token', 0, 'Easing Type', 'The type of easing to apply.\nAllowed values:\n - Bounce: Bouncy, playful motion.\n  - Cubic: The float will change in a cubic curve over time.\n  - EaseIn: The float will start slow, then accelerate.\n  - EaseInOut: The float will start slow, accelerate, then decelerate.\n  - EaseOut: The float will start fast, then decelerate.\n  - Elastic: Spring-like motion.\n  - Exponential: Dramatic acceleration effect.\n  - Linear: The float will have a constant velocity.\n  - Sine: Smooth, natural motion using a sine wave.\n ', {ogn.MetadataKeys.ALLOWED_TOKENS: 'Bounce,Cubic,EaseIn,EaseInOut,EaseOut,Elastic,Exponential,Linear,Sine', 'tokenCategory': 'Enum', ogn.MetadataKeys.ALLOWED_TOKENS_RAW: '["Bounce", "Cubic", "EaseIn", "EaseInOut", "EaseOut", "Elastic", "Exponential", "Linear", "Sine"]', ogn.MetadataKeys.DEFAULT: '"Linear"'}, True, "Linear", False, ''),
        ('inputs:inputMax', 'float', 0, 'Input Max', 'If `Value` equals `Input Max`, the output will be `Output Max`.', {ogn.MetadataKeys.DEFAULT: '1.0'}, True, 1.0, False, ''),
        ('inputs:inputMin', 'float', 0, 'Input Min', 'If `Value` equals `Input Min`, the output will be `Output Min`.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
        ('inputs:outputMax', 'float,float[2],float[3],float[4]', 1, 'Output Max', 'What a `Value` of `Input Max` maps to.', {}, True, None, False, ''),
        ('inputs:outputMin', 'float,float[2],float[3],float[4]', 1, 'Output Min', 'What a `Value` of `Input Min` maps to.', {}, True, None, False, ''),
        ('inputs:shouldReverse', 'bool', 0, 'Should Reverse', 'If true, the easing is applied backwards. If `Value` is coming from a Loop component that is using `pingpong`, hook this up to `isReversing` from that component.', {ogn.MetadataKeys.DEFAULT: 'false'}, False, False, False, ''),
        ('inputs:value', 'float', 0, 'Value', 'The input value to interpolate.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
        ('outputs:output', 'float,float[2],float[3],float[4]', 1, 'Output', 'The final remapped value after applying input normalization, easing, and output mapping.', {}, True, None, False, ''),
    ])

    class tokens:
        Bounce = "Bounce"
        Cubic = "Cubic"
        EaseIn = "EaseIn"
        EaseInOut = "EaseInOut"
        EaseOut = "EaseOut"
        Elastic = "Elastic"
        Exponential = "Exponential"
        Linear = "Linear"
        Sine = "Sine"

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"clampInput", "easingType", "inputMax", "inputMin", "shouldReverse", "value", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = [self._attributes.clampInput, self._attributes.easingType, self._attributes.inputMax, self._attributes.inputMin, self._attributes.shouldReverse, self._attributes.value]
            self._batchedReadValues = [False, "Linear", 1.0, 0.0, False, 0.0]

        @property
        def outputMax(self) -> og.RuntimeAttribute:
            """Get the runtime wrapper class for the attribute inputs.outputMax"""
            return og.RuntimeAttribute(self._attributes.outputMax.get_attribute_data(), self._context, True)

        @outputMax.setter
        def outputMax(self, value_to_set: Any):
            """Assign another attribute's value to outputs.outputMax"""
            if isinstance(value_to_set, og.RuntimeAttribute):
                self.outputMax.value = value_to_set.value
            else:
                self.outputMax.value = value_to_set

        @property
        def outputMin(self) -> og.RuntimeAttribute:
            """Get the runtime wrapper class for the attribute inputs.outputMin"""
            return og.RuntimeAttribute(self._attributes.outputMin.get_attribute_data(), self._context, True)

        @outputMin.setter
        def outputMin(self, value_to_set: Any):
            """Assign another attribute's value to outputs.outputMin"""
            if isinstance(value_to_set, og.RuntimeAttribute):
                self.outputMin.value = value_to_set.value
            else:
                self.outputMin.value = value_to_set

        @property
        def clampInput(self):
            return self._batchedReadValues[0]

        @clampInput.setter
        def clampInput(self, value):
            self._batchedReadValues[0] = value

        @property
        def easingType(self):
            return self._batchedReadValues[1]

        @easingType.setter
        def easingType(self, value):
            self._batchedReadValues[1] = value

        @property
        def inputMax(self):
            return self._batchedReadValues[2]

        @inputMax.setter
        def inputMax(self, value):
            self._batchedReadValues[2] = value

        @property
        def inputMin(self):
            return self._batchedReadValues[3]

        @inputMin.setter
        def inputMin(self, value):
            self._batchedReadValues[3] = value

        @property
        def shouldReverse(self):
            return self._batchedReadValues[4]

        @shouldReverse.setter
        def shouldReverse(self, value):
            self._batchedReadValues[4] = value

        @property
        def value(self):
            return self._batchedReadValues[5]

        @value.setter
        def value(self, value):
            self._batchedReadValues[5] = value

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
        def output(self) -> og.RuntimeAttribute:
            """Get the runtime wrapper class for the attribute outputs.output"""
            return og.RuntimeAttribute(self._attributes.output.get_attribute_data(), self._context, False)

        @output.setter
        def output(self, value_to_set: Any):
            """Assign another attribute's value to outputs.output"""
            if isinstance(value_to_set, og.RuntimeAttribute):
                self.output.value = value_to_set.value
            else:
                self.output.value = value_to_set

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
        self.inputs = RemapDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = RemapDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = RemapDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'lightspeed.trex.logic.Remap'

        @staticmethod
        def compute(context, node):
            def database_valid():
                if db.inputs.outputMax.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute inputs:outputMax is not resolved, compute skipped')
                    return False
                if db.inputs.outputMin.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute inputs:outputMin is not resolved, compute skipped')
                    return False
                if db.outputs.output.type.base_type == og.BaseDataType.UNKNOWN:
                    db.log_warning('Required extended attribute outputs:output is not resolved, compute skipped')
                    return False
                return True
            try:
                per_node_data = RemapDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = RemapDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = RemapDatabase(node)

            try:
                compute_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return RemapDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            RemapDatabase._initialize_per_node_data(node)
            initialize_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = RemapDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                RemapDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            RemapDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            RemapDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "lightspeed.trex.logic.ogn")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Remap")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "Transform")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Smoothly maps a value from one range to another range with customizable easing curves.\n\nRemaps a value from an input range to an output range with optional easing. Values will be normalized (mapped from input range to 0-1), eased (changed from linear to some curve), then mapped (0-1 value to output range).\n\nNote: Input values outside of input range are valid, and easing can lead to the output value being outside of the output range even when input is inside the input range.\n\nInverted ranges (max < min) are supported.")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                RemapDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(RemapDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        RemapDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(RemapDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("lightspeed.trex.logic.Remap")
