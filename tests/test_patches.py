from rest_framework.serializers import Serializer

from drf_nplus import patches


def test_install_is_idempotent():
    patches.install()
    first = Serializer.to_representation
    patches.install()
    assert Serializer.to_representation is first


def test_uninstall_restores_original():
    patches.install()
    patched = Serializer.to_representation
    patches.uninstall()
    assert Serializer.to_representation is not patched
    # Re-install for the rest of the suite
    patches.install()
