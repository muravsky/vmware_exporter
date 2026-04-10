import os

from unittest import mock

from pyVmomi import vim

from vmware_exporter.helpers import batch_fetch_properties, get_bool_env


class FakeView(vim.ManagedObject):

    def __init__(self):
        super().__init__('dummy-moid')

    def Destroy(self):
        pass


def test_get_bool_env():
    # Expected behaviour
    assert get_bool_env('NON_EXISTENT_ENV', True)

    # #102 'bool("False") will evaluate to True in Python'
    os.environ['VSPHERE_COLLECT_VMS'] = "False"
    assert not get_bool_env('VSPHERE_COLLECT_VMS', True)

    # Environment is higher prio than defaults
    os.environ['ENVHIGHERPRIO'] = "True"
    assert get_bool_env('ENVHIGHERPRIO', False)
    assert get_bool_env('ENVHIGHERPRIO', True)

    os.environ['ENVHIGHERPRIO_F'] = "False"
    assert not get_bool_env('ENVHIGHERPRIO_F', False)
    assert not get_bool_env('ENVHIGHERPRIO_F', True)

    # Accent upper and lower case in env vars
    os.environ['ENVHIGHERPRIO_F'] = "false"
    assert not get_bool_env('ENVHIGHERPRIO_F', True)


def test_batch_fetch_properties():
    content = mock.Mock()

    # There is strict parameter checking - this must be a ManagedObject, not a mock,
    # but the real return value has methods with side effects. So we need to use a fake.
    content.viewManager.CreateContainerView.return_value = FakeView()

    mockCustomField1 = mock.Mock()
    mockCustomField1.key = 1
    mockCustomField1.name = 'customAttribute1'
    mockCustomField1.managedObjectType = vim.Datastore

    mockCustomField2 = mock.Mock()
    mockCustomField2.key = 2
    mockCustomField2.name = 'customAttribute2'
    mockCustomField1.managedObjectType = vim.VirtualMachine

    content.customFieldsManager.field = [
        mockCustomField1,
        mockCustomField2,
    ]

    prop1 = mock.Mock()
    prop1.name = 'someprop'
    prop1.val = 1

    prop2 = mock.Mock()
    prop2.name = 'someotherprop'
    prop2.val = 2

    mock_props = mock.Mock()
    mock_props.obj._moId = 'vm:1'
    mock_props.propSet = [prop1, prop2]

    content.propertyCollector.RetrieveContents.return_value = [mock_props]

    results = batch_fetch_properties(
        content,
        vim.Datastore,
        ['someprop', 'someotherprop'],
    )

    assert results == {
        'vm:1': {
            'obj': mock_props.obj,
            'id': 'vm:1',
            'someprop': 1,
            'someotherprop': 2,
        }
    }


def test_batch_fetch_properties_custom_attributes_type_and_key_order():
    content = mock.Mock()
    content.viewManager.CreateContainerView.return_value = FakeView()

    vm_exact = mock.Mock()
    vm_exact.key = 100
    vm_exact.name = 'Team'
    vm_exact.managedObjectType = vim.VirtualMachine

    vm_inherited = mock.Mock()
    vm_inherited.key = 200
    vm_inherited.name = 'Owner'
    vm_inherited.managedObjectType = vim.ManagedEntity

    vm_generic = mock.Mock()
    vm_generic.key = 300
    vm_generic.name = 'Backup'
    vm_generic.managedObjectType = None

    # Same key as vm_exact but for another type: should not override VM mapping.
    ds_conflict = mock.Mock()
    ds_conflict.key = 100
    ds_conflict.name = 'DatastoreTeam'
    ds_conflict.managedObjectType = vim.Datastore

    content.customFieldsManager.field = [ds_conflict, vm_generic, vm_inherited, vm_exact]

    attr_200 = mock.Mock()
    attr_200.key = 200
    attr_200.value = 'owner-a'

    attr_100 = mock.Mock()
    attr_100.key = 100
    attr_100.value = 'team-a'

    attr_300 = mock.Mock()
    attr_300.key = 300
    attr_300.value = 'yes'

    prop_custom = mock.Mock()
    prop_custom.name = 'summary.customValue'
    # Intentionally unsorted input by key.
    prop_custom.val = [attr_200, attr_100, attr_300]

    mock_props = mock.Mock()
    mock_props.obj._moId = 'vm:1'
    mock_props.propSet = [prop_custom]

    content.propertyCollector.RetrieveContents.return_value = [mock_props]

    results = batch_fetch_properties(
        content,
        vim.VirtualMachine,
        ['summary.customValue'],
    )

    assert results['vm:1']['summary.customValue'] == {
        'Team': 'team-a',
        'Owner': 'owner-a',
        'Backup': 'yes',
    }
    assert list(results['vm:1']['summary.customValueByKey'].keys()) == [100, 200, 300]
