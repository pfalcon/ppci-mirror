""" Definitions of arm instructions. """

# pylint: disable=no-member,invalid-name

from .isa import arm_isa, ArmToken, ArmImmToken, Isa
from ..encoding import Instruction, Constructor, Syntax, Operand, Transform
from ...utils.bitfun import encode_imm32
from ...utils.tree import Tree
from .registers import ArmRegister, Coreg, Coproc, RegisterSet, R11
from .registers import R0, R1, R2
from .arm_relocations import Imm24Relocation
from .arm_relocations import LdrImm12Relocation, AdrImm12Relocation


# Patterns:

# Condition patterns:
EQ, NE, CS, CC, MI, PL, VS, VC, HI, LS, GE, LT, GT, LE, AL = range(15)
COND_MAP = {
    'EQ': EQ,
    'NE': NE,
    'CS': CS,
    'CC': CC,
    'MI': MI,
    'PL': PL,
    'VS': VS,
    'VC': VC,
    'HI': HI,
    'LS': LS,
    'GE': GE,
    'LT': LT,
    'GT': GT,
    'LE': LE,
    'AL': AL}


class NoShift(Constructor):
    """ No shift """
    syntax = Syntax([])
    patterns = {'shift_typ': 0, 'shift_imm': 0}


class ShiftLsl(Constructor):
    """ Logical shift left n bits """
    n = Operand('n', int)
    syntax = Syntax([',', ' ', 'lsl', ' ', n])
    patterns = {'shift_typ': 0, 'shift_imm': n}


class ShiftLsr(Constructor):
    """ Logical shift right n bits """
    n = Operand('n', int)
    syntax = Syntax([',', ' ', 'lsr', ' ', n])
    patterns = {'shift_typ': 1, 'shift_imm': n}


class ShiftAsr(Constructor):
    """ Arithmetic shift right n bits """
    n = Operand('n', int)
    syntax = Syntax([',', ' ', 'asr', ' ', n])
    patterns = {'shift_typ': 2, 'shift_imm': n}


# Shift suffix:
shift_modes = (NoShift, ShiftLsl, ShiftLsr, ShiftAsr)


# Instructions:

def inter_twine(a, cond):
    """ Create a permutation for a instruction class """
    # TODO: give this function the right name
    stx = list(a.syntax.syntax)
    ccode = COND_MAP[cond.upper()]
    mnemonic = stx[0] + cond
    stx[0] = mnemonic
    syntax = Syntax(stx)
    patterns = dict(a.patterns)
    patterns['cond'] = ccode
    members = {'syntax': syntax, 'patterns': patterns}
    return type(mnemonic, (a, ), members)


class ArmInstruction(Instruction):
    tokens = [ArmToken]
    isa = arm_isa


class ArmExpand(Transform):
    def forwards(self, value):
        return encode_imm32(value)


class Mov1(ArmInstruction):
    """ Mov Rd, imm16 """
    rd = Operand('rd', ArmRegister, write=True)
    imm = Operand('imm', int)
    tokens = [ArmImmToken]
    syntax = Syntax(['mov', ' ', rd, ',', ' ', imm])
    patterns = {
        'cond': AL, 'opcode': 0b11101, 's': 0, 'rn': 0, 'rd': rd,
        'imm12': ArmExpand(imm)}


class Mov2(ArmInstruction):
    """ Mov register to register """
    rd = Operand('rd', ArmRegister, write=True)
    rm = Operand('rm', ArmRegister, read=True)
    shift = Operand('shift', shift_modes)
    syntax = Syntax(['mov', ' ', rd, ',', ' ', rm, shift])
    patterns = {
        'cond': AL, 'opcode': 0b0001101, 'S': 0, 'Rn': 0, 'Rd': rd,
        'shift_imm': 0, 'shift_typ': 0, 'b4': 0, 'Rm': rm}


Mov2LS = inter_twine(Mov2, 'ls')


class Cmp1(ArmInstruction):
    """ CMP Rn, imm """
    reg = Operand('reg', ArmRegister, read=True)
    imm = Operand('imm', int)
    tokens = [ArmImmToken]
    syntax = Syntax(['cmp', ' ', reg, ',', ' ', imm])
    patterns = {
        'cond': AL, 'opcode': 0b11010, 's': 1, 'rn': reg, 'rd': 0,
        'imm12': ArmExpand(imm)}


class Cmp2(ArmInstruction):
    """ CMP Rn, Rm """
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    shift = Operand('shift', shift_modes)
    syntax = Syntax(['cmp', ' ', rn, ',', ' ', rm, shift])
    patterns = {
        'cond': AL, 'opcode': 0b1010, 'S': 1, 'Rm': rm, 'Rd': 0,
        'b4': 0, 'Rn': rn}


class Mul1(ArmInstruction):
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['mul', ' ', rd, ',', ' ', rn, ',', ' ', rm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = 0b1001
        tokens[0][8:12] = self.rm.num
        tokens[0][16:20] = self.rd.num
        tokens[0].S = 0
        tokens[0].cond = AL
        return tokens[0].encode()


class Sdiv(ArmInstruction):
    """ Encoding A1
        rd = rn / rm

        This instruction is not always present
    """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['sdiv', rd, ',', rn, ',', rm])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = 0b0001
        tokens[0][8:12] = self.rm.num
        tokens[0][12:16] = 0b1111
        tokens[0][16:20] = self.rd.num
        tokens[0][20:28] = 0b1110001
        tokens[0].cond = AL
        return tokens[0].encode()


class Udiv(ArmInstruction):
    """ Encoding A1
        rd = rn / rm
    """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['udiv', rd, ',', rn, ',', rm])
    patterns = {'cond': AL}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = 0b0001
        tokens[0][8:12] = self.rm.num
        tokens[0][12:16] = 0b1111
        tokens[0][16:20] = self.rd.num
        tokens[0][20:28] = 0b1110011
        return tokens.encode()


class Mls(ArmInstruction):
    """ Multiply substract
        Semantics:
        rd = ra - rn * rm
    """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    ra = Operand('ra', ArmRegister, read=True)
    syntax = Syntax(['mls', rd, ',', rn, ',', rm, ',', ra])
    patterns = {'cond': AL}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = 0b1001
        tokens[0][8:12] = self.rm.num
        tokens[0][12:16] = self.ra.num
        tokens[0][16:20] = self.rd.num
        tokens[0][20:28] = 0b00000110
        return tokens.encode()


def make_regregreg(mnemonic, opcode):
    """ Create a new instruction class with three registers as operands """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    shift = Operand('shift', shift_modes)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', rn, ',', ' ', rm, shift])
    patterns = {
        'cond': AL, 'opcode': opcode, 'S': 0, 'Rn': rn, 'Rd': rd, 'b4': 0,
        'Rm': rm}
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'rm': rm,
        'shift': shift, 'patterns': patterns
        }
    return type(mnemonic + '_ins', (ArmInstruction,), members)


Adc = make_regregreg('adc', 0b0000101)
Add = make_regregreg('add', 0b0000100)
And = make_regregreg('and', 0b0000000)
Eor = make_regregreg('eor', 0b0000001)
Orr = make_regregreg('orr', 0b0001100)
Sub = make_regregreg('sub', 0b0000010)


Sub1CC = inter_twine(Sub, 'cc')
Sub1cs = inter_twine(Sub, 'cs')
Sub1NE = inter_twine(Sub, 'ne')


class ShiftBase(ArmInstruction):
    """ ? rd, rn, rm """
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    rm = Operand('rm', ArmRegister, read=True)
    patterns = {'cond': AL, 'S': 0}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][0:4] = self.rn.num
        tokens[0][4:8] = self.opcode
        tokens[0][8:12] = self.rm.num
        tokens[0][12:16] = self.rd.num
        tokens[0][21:28] = 0b1101
        return tokens[0].encode()


class Lsr1(ShiftBase):
    opcode = 0b0011
    syntax = Syntax(
        ['lsr', ShiftBase.rd, ',', ShiftBase.rn, ',', ShiftBase.rm])


Lsr = Lsr1


class Lsl1(ShiftBase):
    opcode = 0b0001
    syntax = Syntax(
        ['lsl', ShiftBase.rd, ',', ShiftBase.rn, ',', ShiftBase.rm])


Lsl = Lsl1


class OpRegRegImm(ArmInstruction):
    """ add rd, rn, imm12 """
    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:12] = encode_imm32(self.imm)
        tokens[0].Rd = self.rd.num
        tokens[0].Rn = self.rn.num
        tokens[0].S = 0  # Set flags
        tokens[0][21:28] = self.opcode
        tokens[0].cond = AL
        return tokens[0].encode()


def make_regregimm(mnemonic, opcode):
    rd = Operand('rd', ArmRegister, write=True)
    rn = Operand('rn', ArmRegister, read=True)
    imm = Operand('imm', int)
    syntax = Syntax([mnemonic, ' ', rd, ',', ' ', rn, ',', ' ', imm])
    members = {
        'syntax': syntax, 'rd': rd, 'rn': rn, 'imm': imm, 'opcode': opcode}
    return type(mnemonic + '_ins', (OpRegRegImm,), members)


AdcImm = make_regregimm('adc', 0b0010101)
AddImm = make_regregimm('add', 0b0010100)
AndImm = make_regregimm('and', 0b0010000)
EorImm = make_regregimm('eor', 0b0010001)
OrrImm = make_regregimm('orr', 0b0011100)
RsbImm = make_regregimm('rsb', 0b0010011)
RscImm = make_regregimm('rsc', 0b0010111)
SbcImm = make_regregimm('sbc', 0b0010110)
SubImm = make_regregimm('sub', 0b0010010)


# Branches:

class BranchBaseRoot(ArmInstruction):
    target = Operand('target', str)

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = self.cond
        tokens[0][24:28] = self.opcode
        return tokens[0].encode()

    def relocations(self):
        return [Imm24Relocation(self.target)]


class BranchBase(BranchBaseRoot):
    opcode = 0b1010


class BranchLinkBase(BranchBaseRoot):
    opcode = 0b1011


class Bl(BranchLinkBase):
    cond = AL
    syntax = Syntax(['bl', ' ', BranchBaseRoot.target])


def make_branch(mnemonic, cond):
    target = Operand('target', str)
    syntax = Syntax([mnemonic, ' ', target])
    members = {
        'syntax': syntax, 'target': target, 'cond': cond}
    return type(mnemonic + '_ins', (BranchBase,), members)


B = make_branch('b', AL)
Beq = make_branch('beq', EQ)
Bgt = make_branch('bgt', GT)
Bge = make_branch('bge', GE)
Bls = make_branch('bls', LS)
Ble = make_branch('ble', LE)
Blt = make_branch('blt', LT)
Bne = make_branch('bne', NE)
Bhs = make_branch('bhs', CS)  # Hs (higher or same) is synonim for CS
Blo = make_branch('blo', CC)  # Lo (unsigned lower) is synonim for CC


class Blx(ArmInstruction):
    """ Branch with link to a subroutine pointer to by register """
    rm = Operand('rm', ArmRegister, read=True)
    syntax = Syntax(['blx', ' ', rm])
    patterns = {'cond': AL, 'Rm': rm}

    def encode(self):
        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        tokens[0][4:28] = 0x12fff3
        return tokens.encode()


def reg_list_to_mask(reg_list):
    mask = 0
    for reg in reg_list:
        mask |= (1 << reg.num)
    return mask


class Push(ArmInstruction):
    reg_list = Operand('reg_list', RegisterSet)
    syntax = Syntax(['push', ' ', reg_list])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0][16:28] = 0b100100101101
        tokens[0][0:16] = reg_list_to_mask(self.reg_list)
        return tokens[0].encode()


class Pop(ArmInstruction):
    reg_list = Operand('reg_list', RegisterSet)
    syntax = Syntax(['pop', ' ', reg_list])

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0][16:28] = 0b100010111101
        tokens[0][0:16] = reg_list_to_mask(self.reg_list)
        return tokens[0].encode()


def LdrPseudo(rt, lab, add_lit):
    """ Ldr rt, =lab ==> ldr rt, [pc, offset in litpool] ... dcd lab """
    lit_lbl = add_lit(lab)
    return Ldr3(rt, lit_lbl)


class LdrStrBase(ArmInstruction):
    rn = Operand('rn', ArmRegister, read=True)
    offset = Operand('offset', int)

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0].Rn = self.rn.num
        tokens[0][25:28] = self.opcode
        tokens[0][22] = self.bit22
        tokens[0][20] = self.bit20
        tokens[0][12:16] = self.rt.num
        tokens[0][24] = 1  # Index
        if self.offset >= 0:
            tokens[0][23] = 1  # U == 1 'add'
            tokens[0][0:12] = self.offset
        else:
            tokens[0][23] = 0
            tokens[0][0:12] = -self.offset
        return tokens.encode()


class Str1(LdrStrBase):
    rt = Operand('rt', ArmRegister, read=True)
    opcode = 0b010
    bit20 = 0
    bit22 = 0
    syntax = Syntax([
        'str', ' ', rt, ',', ' ', '[', LdrStrBase.rn, ',', ' ',
        LdrStrBase.offset, ']'])


class Ldr1(LdrStrBase):
    rt = Operand('rt', ArmRegister, write=True)
    opcode = 0b010
    bit20 = 1
    bit22 = 0
    syntax = Syntax([
        'ldr', ' ', rt, ',', ' ', '[', LdrStrBase.rn, ',', ' ',
        LdrStrBase.offset, ']'])


class Strb(LdrStrBase):
    """ ldrb rt, [rn, offset] # Store byte at address """
    rt = Operand('rt', ArmRegister, read=True)
    opcode = 0b010
    bit20 = 0
    bit22 = 1
    syntax = Syntax([
        'strb', ' ', rt, ',', ' ', '[', LdrStrBase.rn, ',', ' ',
        LdrStrBase.offset, ']'])


class Ldrb(LdrStrBase):
    """ ldrb rt, [rn, offset] """
    rt = Operand('rt', ArmRegister, write=True)
    opcode = 0b010
    bit20 = 1
    bit22 = 1
    syntax = Syntax([
        'ldrb', ' ', rt, ',', ' ', '[', LdrStrBase.rn, ',', ' ',
        LdrStrBase.offset, ']'])


# TODO:
Ldrsb = Ldrb


class Adr(ArmInstruction):
    rd = Operand('rd', ArmRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['adr', rd, ',', label])

    def relocations(self):
        return [AdrImm12Relocation(self.label)]

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0][0:12] = 0  # Filled by linker
        tokens[0][12:16] = self.rd.num
        tokens[0][16:20] = 0b1111
        tokens[0][25] = 1
        return tokens[0].encode()


class Ldr3(ArmInstruction):
    """ Load PC relative constant value
        LDR rt, label
        encoding A1
    """
    rt = Operand('rt', ArmRegister, write=True)
    label = Operand('label', str)
    syntax = Syntax(['ldr', ' ', rt, ',', ' ', label])

    def relocations(self):
        return [LdrImm12Relocation(self.label)]

    def encode(self):
        tokens = self.get_tokens()
        tokens[0].cond = AL
        tokens[0][0:12] = 0  # Filled by linker
        tokens[0][12:16] = self.rt.num
        tokens[0][16:23] = 0b0011111
        tokens[0][24:28] = 0b0101
        return tokens[0].encode()


class McrBase(ArmInstruction):
    """ Mov arm register to coprocessor register """
    def encode(self):
        tokens = self.get_tokens()
        tokens[0][0:4] = self.crm.num
        tokens[0][4] = 1
        tokens[0][5:8] = self.opc2
        tokens[0][8:12] = self.coproc.num
        tokens[0][12:16] = self.rt.num
        tokens[0][16:20] = self.crn.num
        tokens[0][20] = self.b20
        tokens[0][21:24] = self.opc1
        tokens[0][24:28] = 0b1110
        tokens[0].cond = AL
        return tokens[0].encode()


class Mcr(McrBase):
    """ Move from register to co processor register """
    coproc = Operand('coproc', Coproc, read=True)
    opc1 = Operand('opc1', int)
    rt = Operand('rt', ArmRegister, read=True)
    crn = Operand('crn', Coreg, read=True)
    crm = Operand('crm', Coreg, read=True)
    opc2 = Operand('opc2', int)
    b20 = 0
    syntax = Syntax(
        ['mcr', coproc, ',', opc1, ',', rt, ',', crn, ',', crm, ',', opc2])


class Mrc(McrBase):
    coproc = Operand('coproc', Coproc, read=True)
    opc1 = Operand('opc1', int)
    rt = Operand('rt', ArmRegister, write=True)
    crn = Operand('crn', Coreg, read=True)
    crm = Operand('crm', Coreg, read=True)
    opc2 = Operand('opc2', int)
    b20 = 1
    syntax = Syntax(
        ['mrc', coproc, ',', opc1, ',', rt, ',', crn, ',', crm, ',', opc2])


# Instruction selection patterns:
@arm_isa.pattern(
    'mem', 'ADDI32(reg, CONSTI32)', size=0,
    condition=lambda t: t[1].value < 256)
def pattern_mem_reg_offset(context, tree, c0):
    offset = tree.children[0].children[1].value
    return c0, offset


@arm_isa.pattern('mem', 'FPRELU32', size=0, cycles=0, energy=0)
def pattern_mem_fprel32(context, tree):
    offset = tree.value.offset
    return R11, offset


@arm_isa.pattern('mem', 'reg', size=0, cycles=0, energy=0)
def pattern_mem_reg(context, tree, c0):
    return c0, 0


@arm_isa.pattern('stm', 'STRI32(mem, reg)', size=4)
@arm_isa.pattern('stm', 'STRU32(mem, reg)', size=4)
def pattern_str32(self, tree, c0, c1):
    base_reg, offset = c0
    self.emit(Str1(c1, base_reg, offset))


@arm_isa.pattern('stm', 'STRI8(mem, reg)', size=4)
@arm_isa.pattern('stm', 'STRU8(mem, reg)', size=4)
def pattern_str8(context, tree, c0, c1):
    base_reg, offset = c0
    context.emit(Strb(c1, base_reg, offset))


@arm_isa.pattern('reg', 'MOVI32(reg)', size=4)
@arm_isa.pattern('reg', 'MOVU32(reg)', size=4)
def pattern_mov32(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@arm_isa.pattern('reg', 'MOVI8(reg)', size=4)
@arm_isa.pattern('reg', 'MOVU8(reg)', size=4)
def pattern_mov8(context, tree, c0):
    context.move(tree.value, c0)
    return tree.value


@arm_isa.pattern('stm', 'JMP', size=2)
def pattern_jmp(context, tree):
    tgt = tree.value
    context.emit(B(tgt.name, jumps=[tgt]))


@arm_isa.pattern('reg', 'REGI32', size=0, cycles=0, energy=0)
@arm_isa.pattern('reg', 'REGU32', size=0, cycles=0, energy=0)
def pattern_reg32(context, tree):
    return tree.value


@arm_isa.pattern('reg', 'REGI8', size=0, cycles=0, energy=0)
@arm_isa.pattern('reg', 'REGU8', size=0, cycles=0, energy=0)
def pattern_reg8(context, tree):
    return tree.value


@arm_isa.pattern('reg', 'U32TOU32(reg)', size=0)
@arm_isa.pattern('reg', 'U32TOI32(reg)', size=0)
@arm_isa.pattern('reg', 'I32TOI32(reg)', size=0)
@arm_isa.pattern('reg', 'I32TOU32(reg)', size=0)
def pattern_i32toi32(self, tree, c0):
    return c0


@arm_isa.pattern('reg', 'I8TOI32(reg)', size=0)
@arm_isa.pattern('reg', 'U8TOI32(reg)', size=0)
def pattern_i8toi32(self, tree, c0):
    # TODO: do something?
    # Sign extend for example?
    return c0


@arm_isa.pattern('reg', 'I32TOI8(reg)', size=0)
@arm_isa.pattern('reg', 'I32TOU8(reg)', size=0)
def pattern_i32toi8(context, tree, c0):
    d2 = context.new_reg(ArmRegister)
    context.emit(AndImm(d2, c0, 0xff))
    return d2


@arm_isa.pattern('reg', 'CONSTI32', size=8)
@arm_isa.pattern('reg', 'CONSTU32', size=8)
def pattern_const32(context, tree):
    d = context.new_reg(ArmRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Ldr3(d, ln))
    return d


@arm_isa.pattern(
    'reg', 'CONSTU32', size=4, condition=lambda t: t.value in range(256))
@arm_isa.pattern(
    'reg', 'CONSTI32', size=4, condition=lambda t: t.value in range(256))
def pattern_const32_1(context, tree):
    d = context.new_reg(ArmRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 256 and c0 >= 0
    context.emit(Mov1(d, c0))
    return d


@arm_isa.pattern('reg', 'CONSTI8', size=4, condition=lambda t: t.value < 256)
@arm_isa.pattern('reg', 'CONSTU8', size=4, condition=lambda t: t.value < 256)
def pattern_const8_1(context, tree):
    d = context.new_reg(ArmRegister)
    c0 = tree.value
    assert isinstance(c0, int)
    assert c0 < 256 and c0 >= 0
    context.emit(Mov1(d, c0))
    return d


@arm_isa.pattern('stm', 'CJMPI32(reg, reg)', size=2)
@arm_isa.pattern('stm', 'CJMPU32(reg, reg)', size=2)
@arm_isa.pattern('stm', 'CJMPI16(reg, reg)', size=2)
@arm_isa.pattern('stm', 'CJMPU16(reg, reg)', size=2)
@arm_isa.pattern('stm', 'CJMPI8(reg, reg)', size=2)
@arm_isa.pattern('stm', 'CJMPU8(reg, reg)', size=2)
def pattern_cjmp(context, tree, c0, c1):
    op, yes_label, no_label = tree.value
    opnames = {"<": Blt, ">": Bgt, "==": Beq, "!=": Bne, ">=": Bge}
    Bop = opnames[op]
    context.emit(Cmp2(c0, c1, NoShift()))
    jmp_ins = B(no_label.name, jumps=[no_label])
    context.emit(Bop(yes_label.name, jumps=[yes_label, jmp_ins]))
    context.emit(jmp_ins)


@arm_isa.pattern('reg', 'ADDI32(reg, reg)', size=2)
@arm_isa.pattern('reg', 'ADDU32(reg, reg)', size=2)
def pattern_add32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Add(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern('reg', 'ADDI8(reg, reg)', size=4)
@arm_isa.pattern('reg', 'ADDU8(reg, reg)', size=4)
def pattern_add8(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Add(d, c0, c1, NoShift()))
    d2 = context.new_reg(ArmRegister)
    context.emit(AndImm(d2, d, 0xff))
    return d2


@arm_isa.pattern(
    'reg', 'ADDI32(reg, CONSTI32)', size=4,
    condition=lambda t: t.children[1].value in range(256))
def pattern_add32_1(context, tree, c0):
    d = context.new_reg(ArmRegister)
    c1 = tree.children[1].value
    context.emit(AddImm(d, c0, c1))
    return d


@arm_isa.pattern(
    'reg', 'ADDI32(CONSTI32, reg)', size=4,
    condition=lambda t: t.children[0].value in range(256))
def pattern_add32_2(context, tree, c0):
    d = context.new_reg(ArmRegister)
    c1 = tree.children[0].value
    context.emit(AddImm(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'SUBI32(reg, reg)', size=4)
@arm_isa.pattern('reg', 'SUBU32(reg, reg)', size=4)
def pattern_sub32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Sub(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern('reg', 'SUBI8(reg, reg)', size=4)
def pattern_sub8(context, tree, c0, c1):
    # TODO: temporary fix this with an 32 bits sub
    d = context.new_reg(ArmRegister)
    context.emit(Sub(d, c0, c1, NoShift()))
    d2 = context.new_reg(ArmRegister)
    context.emit(AndImm(d2, d, 0xff))
    return d2


@arm_isa.pattern('reg', 'LABEL', size=8)
def pattern_label(context, tree):
    d = context.new_reg(ArmRegister)
    ln = context.frame.add_constant(tree.value)
    context.emit(Ldr3(d, ln))
    return d


@arm_isa.pattern('reg', 'FPRELU32', size=4, cycles=2, energy=2)
def pattern_fprel32(context, tree):
    d = context.new_reg(ArmRegister)
    c1 = tree.value.offset
    assert isinstance(c1, int)
    if c1 in range(-255, 256):
        if c1 >= 0:
            context.emit(AddImm(d, R11, c1))
        else:
            context.emit(SubImm(d, R11, -c1))
    else:
        d2 = context.new_reg(ArmRegister)
        ln = context.frame.add_constant(c1)
        context.emit(Ldr3(d2, ln))
        context.emit(Add(d, R11, d2, NoShift()))
    return d


@arm_isa.pattern('reg', 'LDRI8(mem)', size=4)
def pattern_ldr_i8(context, tree, c0):
    d = context.new_reg(ArmRegister)
    base_reg, offset = c0
    context.emit(Ldrsb(d, base_reg, offset))
    return d


@arm_isa.pattern('reg', 'LDRU8(mem)', size=4)
def pattern_ldr_u8(context, tree, c0):
    d = context.new_reg(ArmRegister)
    base_reg, offset = c0
    context.emit(Ldrb(d, base_reg, offset))
    return d


@arm_isa.pattern('reg', 'LDRI16(mem)', size=4, energy=8)
def pattern_ldr_i16(context, tree, c0):
    d = context.new_reg(ArmRegister)
    base_reg, offset = c0
    raise NotImplementedError('ldrsh')
    # context.emit(Ldrsh(d, base_reg, offset))
    return d


@arm_isa.pattern('reg', 'LDRU16(mem)', size=4, energy=8)
def pattern_ldr_u16(context, tree, c0):
    d = context.new_reg(ArmRegister)
    base_reg, offset = c0
    raise NotImplementedError('ldrh')
    # context.emit(Ldrh(d, base_reg, offset))
    return d


@arm_isa.pattern('reg', 'LDRI32(mem)', size=4)
@arm_isa.pattern('reg', 'LDRU32(mem)', size=4)
def pattern_ld32(context, tree, c0):
    d = context.new_reg(ArmRegister)
    base_reg, offset = c0
    context.emit(Ldr1(d, base_reg, offset))
    return d


@arm_isa.pattern('reg', 'ANDI8(reg, reg)', size=4)
@arm_isa.pattern('reg', 'ANDU8(reg, reg)', size=4)
@arm_isa.pattern('reg', 'ANDI16(reg, reg)', size=4)
@arm_isa.pattern('reg', 'ANDU16(reg, reg)', size=4)
@arm_isa.pattern('reg', 'ANDI32(reg, reg)', size=4)
@arm_isa.pattern('reg', 'ANDU32(reg, reg)', size=4)
def pattern_and(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(And(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern('reg', Tree('ORI32', Tree('reg'), Tree('reg')), size=4)
@arm_isa.pattern('reg', Tree('ORU32', Tree('reg'), Tree('reg')), size=4)
def pattern_or32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Orr(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern('reg', 'SHRI32(reg, reg)', size=4)
@arm_isa.pattern('reg', 'SHRU32(reg, reg)', size=4)
def pattern_shr32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Lsr1(d, c0, c1))
    return d


@arm_isa.pattern('reg', Tree('SHLI32', Tree('reg'), Tree('reg')), size=4)
@arm_isa.pattern('reg', Tree('SHLU32', Tree('reg'), Tree('reg')), size=4)
def pattern_shl32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Lsl1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'MULI32(reg, reg)', size=4)
@arm_isa.pattern('reg', 'MULU32(reg, reg)', size=4)
def pattern_mul32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Mul1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'LDRI32(ADDI32(reg, CONSTI32))', size=4)
def pattern_ldr32(context, tree, c0):
    d = context.new_reg(ArmRegister)
    c1 = tree.children[0].children[1].value
    assert isinstance(c1, int)
    context.emit(Ldr1(d, c0, c1))
    return d


@arm_isa.pattern('reg', 'DIVI32(reg, reg)')
def pattern_div32(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    # Generate call into runtime lib function!
    context.move(R1, c0)
    context.move(R2, c1)
    context.emit(Bl('__sdiv'))
    context.move(d, R0)
    return d


@arm_isa.pattern('reg', 'REMI32(reg, reg)')
def pattern_rem32(context, tree, c0, c1):
    # Implement remainder as a combo of div and mls (multiply substract)
    d = context.new_reg(ArmRegister)
    context.move(R1, c0)
    context.move(R2, c1)
    context.emit(Bl('__sdiv'))
    context.move(d, R0)
    d2 = context.new_reg(ArmRegister)
    context.emit(Mls(d2, d, c1, c0))
    return d2


@arm_isa.pattern('reg', 'XORI8(reg, reg)', size=4)
@arm_isa.pattern('reg', 'XORU8(reg, reg)', size=4)
@arm_isa.pattern('reg', 'XORI16(reg, reg)', size=4)
@arm_isa.pattern('reg', 'XORU16(reg, reg)', size=4)
@arm_isa.pattern('reg', 'XORI32(reg, reg)', size=4)
@arm_isa.pattern('reg', 'XORU32(reg, reg)', size=4)
def pattern_xor(context, tree, c0, c1):
    d = context.new_reg(ArmRegister)
    context.emit(Eor(d, c0, c1, NoShift()))
    return d


@arm_isa.pattern('reg', 'NEGI32(reg)', size=4)
def pattern_neg32(context, tree, c0):
    d = context.new_reg(ArmRegister)
    # Implement as rsb with immediate value
    context.emit(RsbImm(d, c0, 0))
    return d


@arm_isa.pattern('reg', 'INVI32(reg)', size=4)
def pattern_inv32(context, tree, c0):
    d = context.new_reg(ArmRegister)
    context.move(R1, c0)
    context.emit(Bl('__inv32'))
    context.move(d, R0)
    return d


# TODO: implement DIVI32 by library call.
# TODO: Do that here, or in irdag?


isa_with_div = Isa()


@isa_with_div.pattern('reg', 'DIVI32(reg, reg)', size=4)
def pattern_23(self, tree, c0, c1):
    d = self.new_reg(ArmRegister)
    self.emit(Udiv, dst=[d], src=[c0, c1])
    return d


@isa_with_div.pattern('reg', 'REMI32(reg, reg)', size=4)
def pattern_24(self, tree, c0, c1):
    # Implement remainder as a combo of div and mls (multiply substract)
    d = self.new_reg(ArmRegister)
    self.emit(Udiv, dst=[d], src=[c0, c1])
    d2 = self.new_reg(ArmRegister)
    self.emit(Mls, dst=[d2], src=[d, c1, c0])
    return d2
