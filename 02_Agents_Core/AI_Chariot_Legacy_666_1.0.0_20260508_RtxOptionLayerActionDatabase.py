"""Support for simplified access to data on nodes of type lightspeed.trex.logic.RtxOptionLayerAction

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Activates and controls configuration layers at runtime based on game conditions.

Controls an RtxOptionLayer by name, allowing
dynamic enable/disable, strength adjustment, and threshold control. This can be used to activate configuration layers at
runtime based on game state or other conditions.

The layer is created if it doesn't exist, and managed with reference counting.
If
two components specify the same priority and config path, they will both control the same layer (for enabled components,
uses the MAX of the blend strengths and the MIN of the blend thresholds).
If two components specify the same priority but
different config paths, the layers will be prioritized alphabetically (a.conf will override values from z.conf).
"""

import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class RtxOptionLayerActionDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type lightspeed.trex.logic.RtxOptionLayerAction

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.blendStrength
            inputs.blendThreshold
            inputs.configPath
            inputs.enabled
            inputs.priority
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
        ('inputs:blendStrength', 'float', 0, 'Blend Strength', "The blend strength for the option layer (0.0 = no effect, 1.0 = full effect.)\n\nLowest priority layer uses LERP to blend with default value, then each higher priority layer uses LERP to blend with the previous layer's result.\n\nIf multiple components control the same layer, the MAX blend strength will be used.", {ogn.MetadataKeys.DEFAULT: '1.0'}, False, 1.0, False, ''),
        ('inputs:blendThreshold', 'float', 0, 'Blend Threshold', 'The blend threshold for non-float options (0.0 to 1.0). Non-float options are only applied when blend strength exceeds this threshold. If multiple components control the same layer, the MINIMUM blend threshold will be used.', {ogn.MetadataKeys.DEFAULT: '0.1'}, False, 0.1, False, ''),
        ('inputs:configPath', 'token', 0, 'Config Path', 'The config file for the RtxOptionLayer to control.', {'tokenCategory': 'AssetPath', ogn.MetadataKeys.DEFAULT: '""'}, True, "", False, ''),
        ('inputs:enabled', 'bool', 0, 'Enabled', 'If true, the option layer is enabled and its settings are applied. If false, the layer is disabled. If multiple components control the same layer, it will be enabled if ANY of them request it.', {ogn.MetadataKeys.DEFAULT: 'true'}, False, True, False, ''),
        ('inputs:priority', 'float', 0, 'Priority', 'The priority for the option layer. Numbers are rounded to the nearest positive integer. Higher values are blended on top of lower values. If two components specify the same priority but different config paths, the layers will be prioritized alphabetically (a.conf will override values from z.conf).', {ogn.MetadataKeys.DEFAULT: '10000.0'}, False, 10000.0, False, ''),
    ])

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"blendStrength", "blendThreshold", "configPath", "enabled", "priority", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = [self._attributes.blendStrength, self._attributes.blendThreshold, self._attributes.configPath, self._attributes.enabled, self._attributes.priority]
            self._batchedReadValues = [1.0, 0.1, "", True, 10000.0]

        @property
        def blendStrength(self):
            return self._batchedReadValues[0]

        @blendStrength.setter
        def blendStrength(self, value):
            self._batchedReadValues[0] = value

        @property
        def blendThreshold(self):
            return self._batchedReadValues[1]

        @blendThreshold.setter
        def blendThreshold(self, value):
            self._batchedReadValues[1] = value

        @property
        def configPath(self):
            return self._batchedReadValues[2]

        @configPath.setter
        def configPath(self, value):
            self._batchedReadValues[2] = value

        @property
        def enabled(self):
            return self._batchedReadValues[3]

        @enabled.setter
        def enabled(self, value):
            self._batchedReadValues[3] = value

        @property
        def priority(self):
            return self._batchedReadValues[4]

        @priority.setter
        def priority(self, value):
            self._batchedReadValues[4] = value

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
        self.inputs = RtxOptionLayerActionDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = RtxOptionLayerActionDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = RtxOptionLayerActionDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'lightspeed.trex.logic.RtxOptionLayerAction'

        @staticmethod
        def compute(context, node):
            def database_valid():
                return True
            try:
                per_node_data = RtxOptionLayerActionDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = RtxOptionLayerActionDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = RtxOptionLayerActionDatabase(node)

            try:
                compute_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return RtxOptionLayerActionDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            RtxOptionLayerActionDatabase._initialize_per_node_data(node)
            initialize_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = RtxOptionLayerActionDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                RtxOptionLayerActionDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            RtxOptionLayerActionDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            RtxOptionLayerActionDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "lightspeed.trex.logic.ogn")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Rtx Option Layer Action")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "Act")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Activates and controls configuration layers at runtime based on game conditions.\n\nControls an RtxOptionLayer by name, allowing dynamic enable/disable, strength adjustment, and threshold control. This can be used to activate configuration layers at runtime based on game state or other conditions.\n\nThe layer is created if it doesn't exist, and managed with reference counting.\nIf two components specify the same priority and config path, they will both control the same layer (for enabled components, uses the MAX of the blend strengths and the MIN of the blend thresholds).\nIf two components specify the same priority but different config paths, the layers will be prioritized alphabetically (a.conf will override values from z.conf).")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                RtxOptionLayerActionDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(RtxOptionLayerActionDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        RtxOptionLayerActionDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(RtxOptionLayerActionDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("lightspeed.trex.logic.RtxOptionLayerAction")
