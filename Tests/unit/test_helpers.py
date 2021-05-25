from FESTIM.helpers import help_key, find_material_from_id
import pytest


def test_help_key():
    """Tests the function help_key() with several entries
    """
    help_key("mesh_parameters")
    help_key("temperature")
    help_key("volumes")
    help_key("surfaces")
    help_key("E_p")


def test_find_material_from_id():
    """Tests the function find_material_from_id() for cases with one id per
    material
    """
    materials = [
        {
            "id": 1
        },
        {
            "id": 2
        },
    ]
    assert find_material_from_id(materials, 1) == materials[0]
    assert find_material_from_id(materials, 2) == materials[1]


def test_find_material_from_id_with_several_ids():
    """Tests the function find_material_from_id() for cases with several ids
    per material
    """
    materials = [
        {
            "id": [1, 2]
        },
    ]
    assert find_material_from_id(materials, 1) == materials[0]
    assert find_material_from_id(materials, 2) == materials[0]


def test_find_material_from_id_unfound_id():
    """
    Tests the function find_material_from_id with a list of materials
    without the searched ID
        - check that an error is rasied
    """
    materials = [
        {"id": 5},
        {"id": 2},
        {"id": -1},
    ]
    id_test = 1
    with pytest.raises(ValueError,
                       match="Couldn't find ID {}".format(id_test)):
        find_material_from_id(materials, id_test)