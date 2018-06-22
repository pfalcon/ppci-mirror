import io
from ppci import wasm
from ppci.api import ir_to_object, get_current_arch
from ppci.utils.codepage import load_obj
from ppci.binutils.outstream import TextOutputStream

from ppci.wasm import wasm_to_ir, export_wasm_example
from ppci.wasm.instantiate import instantiate


wasm_module = wasm.Module(
    ('import', 'py', 'add', ('func', '$add', ('param', 'i64', 'i64'), ('result', 'i64'))),
    ('func', ('export', 'main'), ('param', 'i64'), ('result', 'i64'),
        ('get_local', 0),
        ('i64.const', 42),
        ('call', '$add'),
    ),
    ('func', ('export', 'add'), ('param', 'i64', 'i64'), ('result', 'i64'),
        ('get_local', 0),
        ('get_local', 1),
        ('call', '$add'),
    ),
)

print(wasm_module.to_string())

arch = get_current_arch()
ppci_module = wasm_to_ir(wasm_module, arch.info.get_type_info('ptr'))
ppci_module.display()

print('using this arch: ', arch)
f = io.StringIO()
txt_stream = TextOutputStream(f=f, add_binary=True)
obj = ir_to_object([ppci_module], arch, debug=True, outstream=txt_stream)
print(f.getvalue())

def my_add(x: int, y: int) -> int:
    print('my add called', x, y)
    return x + y + 1

# Run in memory
imports = {
    'py_add': my_add
}

native_module = load_obj(obj, imports=imports)
print(dir(native_module))
result = getattr(native_module, 'add')(42, 42)
print(result, '(should be 85)')


# This way a wasm module can be loaded analog to javascript:
instance = instantiate(
    wasm_module,
    {
        'py': {
            'add': my_add,
        }
    })

print(instance.exports.main(1337), '(should be 1380)')
print(instance.exports.add(1, 1), '(should be 3)')
