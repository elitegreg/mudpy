def execfile(file, globals=globals(), locals=locals()):
    with open(file, "r") as fh:
        code = compile(fh.read() + "\n", file, 'exec')
        exec(code, globals, locals)

