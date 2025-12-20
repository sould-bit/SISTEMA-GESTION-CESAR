#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

try:
    from tests.conftest import *
    print("✅ Importaciones de conftest OK")
except Exception as e:
    print(f"❌ Error importando conftest: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services import AuthService
    print("✅ Importación de AuthService OK")
except Exception as e:
    print(f"❌ Error importando AuthService: {e}")

try:
    from app.services import CategoryService
    print("✅ Importación de CategoryService OK")
except Exception as e:
    print(f"❌ Error importando CategoryService: {e}")

try:
    import pytest
    print(f"✅ Pytest disponible: {pytest.__version__}")
except Exception as e:
    print(f"❌ Pytest no disponible: {e}")
