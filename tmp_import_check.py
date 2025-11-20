import importlib, sys, traceback
mods=['qt_app.menu_principal_qt','qt_app.menu_sistemas_qt','qt_app.sistemas.cramer_qt','qt_app.sistemas.gauss_jordan_qt']
ok=True
for m in mods:
    try:
        importlib.import_module(m)
        print(m, 'OK')
    except Exception as e:
        print(m, 'ERROR', type(e).__name__, e)
        traceback.print_exc()
        ok=False
sys.exit(0 if ok else 1
)