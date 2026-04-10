# autopep8'd
import os
from pyVmomi import vmodl


def get_bool_env(key: str, default: bool):
    value = os.environ.get(key, default)
    return value if type(value) == bool else value.lower() == 'true'


def _managed_object_type_matches(field_type, obj_type):
    """
    Return True if a custom field declared for ``field_type`` applies to ``obj_type``.
    Handles exact matches, generic fields (None) and inheritance-based matches.
    """
    if field_type is None:
        return True

    if field_type == obj_type:
        return True

    try:
        return issubclass(obj_type, field_type)
    except TypeError:
        return False


def _build_custom_field_key_name_map(content, obj_type):
    """
    Build a deterministic key -> name map for custom attributes applicable to obj_type.

    If a key is exposed by multiple field definitions, prefer the most specific type:
    exact obj_type > inherited type > generic(None).
    """
    key_name_with_priority = {}

    manager = getattr(content, 'customFieldsManager', None)
    fields = getattr(manager, 'field', None)

    if not fields:
        return {}

    for field in fields:
        key = getattr(field, 'key', None)
        name = getattr(field, 'name', None)
        managed_type = getattr(field, 'managedObjectType', None)

        if key is None or name is None:
            continue

        if not _managed_object_type_matches(managed_type, obj_type):
            continue

        if managed_type == obj_type:
            priority = 3
        elif managed_type is None:
            priority = 1
        else:
            priority = 2

        current = key_name_with_priority.get(key)
        if current is None or priority > current[1]:
            key_name_with_priority[key] = (name, priority)

    return {
        key: value[0]
        for key, value in sorted(key_name_with_priority.items(), key=lambda item: item[0])
    }


def batch_fetch_properties(content, obj_type, properties):
    view_ref = content.viewManager.CreateContainerView(
        container=content.rootFolder,
        type=[obj_type],
        recursive=True
    )

    """
        Gathering all custom attibutes names are stored as key (integer) in CustomFieldsManager
        We do not want those keys, but the names. So here the names and keys are gathered to
        be translated later
    """
    if ('customValue' in properties) or ('summary.customValue' in properties):
        allCustomAttributesNames = _build_custom_field_key_name_map(content, obj_type)

    try:
        PropertyCollector = vmodl.query.PropertyCollector

        # Describe the list of properties we want to fetch for obj_type
        property_spec = PropertyCollector.PropertySpec()
        property_spec.type = obj_type
        property_spec.pathSet = properties

        # Describe where we want to look for obj_type
        traversal_spec = PropertyCollector.TraversalSpec()
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__

        obj_spec = PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True
        obj_spec.selectSet = [traversal_spec]

        filter_spec = PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]
        filter_spec.propSet = [property_spec]

        props = content.propertyCollector.RetrieveContents([filter_spec])

    finally:
        view_ref.Destroy()

    results = {}
    for obj in props:
        properties = {}
        properties['obj'] = obj.obj
        properties['id'] = obj.obj._moId

        for prop in obj.propSet:

            """
                if it's a custom value property for vms (summary.customValue), hosts (summary.customValue)
                or datastores (customValue) - we store all attributes together in a python dict and
                translate its name key to name
            """
            if 'customValue' in prop.name:
                by_key_name = '{}ByKey'.format(prop.name)

                properties[prop.name] = {}
                properties[by_key_name] = {}

                if not prop.val:
                    continue

                for attribute in sorted(prop.val, key=lambda item: getattr(item, 'key', 0)):
                    attr_key = getattr(attribute, 'key', None)
                    if attr_key is None:
                        continue
                    attr_value = str(attribute.value).replace('\n', ' ').replace('\r', ' ').strip() \
                        if attribute.value is not None else 'n/a'
                    properties[by_key_name][attr_key] = attr_value

                    if attr_key in allCustomAttributesNames:
                        properties[prop.name][allCustomAttributesNames[attr_key]] = attr_value

            elif 'triggeredAlarmState' == prop.name:
                """
                    triggered alarms
                """
                try:
                    alarms = list(
                        'triggeredAlarm:{}:{}'.format(item.alarm.info.systemName.split('.')[1], item.overallStatus)
                        for item in prop.val
                    )
                except Exception:
                    alarms = ['triggeredAlarm:AlarmsUnavailable:yellow']

                properties[prop.name] = ','.join(alarms)

            elif 'runtime.healthSystemRuntime.systemHealthInfo.numericSensorInfo' == prop.name:
                """
                    handle numericSensorInfo
                """
                sensors = list(
                    'numericSensorInfo:name={}:type={}:sensorStatus={}:value={}:unitModifier={}:unit={}'.format(
                        item.name,
                        item.sensorType,
                        item.healthState.key,
                        item.currentReading,
                        item.unitModifier,
                        item.baseUnits.lower()
                    )
                    for item in prop.val
                )
                properties[prop.name] = ','.join(sensors)

            elif prop.name in [
                'runtime.healthSystemRuntime.hardwareStatusInfo.cpuStatusInfo',
                'runtime.healthSystemRuntime.hardwareStatusInfo.memoryStatusInfo',
            ]:
                """
                    handle hardwareStatusInfo
                """
                sensors = list(
                    'numericSensorInfo:name={}:type={}:sensorStatus={}:value={}:unitModifier={}:unit={}'.format(
                        item.name,
                        "n/a",
                        item.status.key,
                        "n/a",
                        "n/a",
                        "n/a",
                    )
                    for item in prop.val
                )
                properties[prop.name] = ','.join(sensors)

            else:
                properties[prop.name] = prop.val

        results[obj.obj._moId] = properties

    return results
