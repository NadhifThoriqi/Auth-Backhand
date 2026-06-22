"""
Module:
    core/enums.py
Deskripsi:
    Mendefinisikan enumerasi (enum) yang digunakan di seluruh aplikasi
    sebagai nilai konstan untuk kolom-kolom tertentu di database.
"""

from enum import StrEnum


class Role(StrEnum):
    """
    Enumerasi peran (role) pengguna dalam sistem.

    Values:
        ADMIN: Peran administrator dengan akses penuh.
        BUYER: Peran pembeli/pengguna biasa (default).
    """

    ADMIN = "admin"
    BUYER = "buyer"
