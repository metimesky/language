import parser
import transpiler
from cps import Call, Lambda, Assign, Variable, Constant, Environ, null, true, false

# call = Call([arguments]), call[i]
# lambda = Lambda([arguments], body), lambda[i]
# Assign(var, val, body)
# Variable(name, value)
# Constant(value)

def main():
    mks = []
    env = Environ()
    ret = env.new_argument("cont", False)
    var = null
    for expr in open_list('demo'):
        var = continuate(mks, expr, env)
    program = env.close(compose(mks, Call([ret, var])))
    program = program.coalesce()
    for var in env.unbound:
        var.glob = True
    source = transpiler.transpile(program)
    open('demo.c', 'w').write(source)

constants = {'null': null, 'true':true, 'false':false}
def continuate(mks, expr, env):
    if ismacro2(expr, '=') and expr[0].group == 'symbol':
        var = env.get_local(expr[0].value)
        val = continuate(mks, expr[2], env)
        mks.append(lambda cont: Assign(var, val, cont))
        return val
    if ismacro2(expr, ':=') and expr[0].group == 'symbol':
        var = env.lookup(expr[0].value)
        val = continuate(mks, expr[2], env)
        mks.append(lambda cont: Assign(var, val, cont))
        return val
    if ismacro(expr, 'func'):
        env = env.new_environ()
        ret = env.new_argument('cont', False)
        smks = []
        for sym in expr[1]:
            assert sym.group == 'symbol'
            env.new_argument(sym.value)
        var = null
        for subexpr in expr[2:]:
            var = continuate(smks, subexpr, env)
        return env.close(compose(smks, Call([ret, var])))
    if expr.group == 'list':
        arglist = [continuate(mks, a, env) for a in expr]
        callee  = arglist.pop(0)
        retval  = Variable()
        mks.append(lambda cont: Call([callee, Lambda([retval], cont)] + arglist))
        return retval
    if expr.group == 'symbol':
        if expr.value in constants:
            return constants[expr.value]
        return env.lookup(expr.value)
    if expr.group == 'integer':
        return Constant(expr.value)
    if expr.group == 'double':
        return Constant(expr.value)
    return Exception("what is {}?".format(expr))

def ismacro(expr, name):
    return expr.group == 'list' and len(expr) > 0 and expr[0].value == name

def ismacro2(expr, name):
    return expr.group == 'list' and len(expr) > 2 and expr[1].value == name

def open_list(path):
    with open(path, 'r') as fd:
        return parser.parse(fd.read())

def compose(mks, cont):
    for fn in reversed(mks):
        cont = fn(cont)
    return cont

if __name__ == '__main__':
    main()
