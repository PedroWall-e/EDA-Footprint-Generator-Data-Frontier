"""Emite o NINA_B406.yaml em grupos_pads — 14 corridas em vez de 71 pads.

Cada bloco espelha uma linha da Table 22. As cotas entram como NUMEROS DO
DATASHEET (H, F, R, M, N, Q, S, T, U, Y, K, L, P, ZA1, ZA2, ZB), nao como
coordenadas calculadas.
"""
import json
import os
import sys

SC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SC)
from derivar_nina import (A, B, D, E, F, H, I, J, K, L, M, N, O, P, Q, R, S,
                          T, U, Y, ZA1, ZA2, ZB, ZL, VS)

_p = json.load(open(os.path.join(SC, 'pinagem.json'), encoding='utf-8'))
PINAGEM = {int(k): tuple(v) for k, v in _p.items()}
for n in range(56, 72):
    PINAGEM[n] = ('GND', '-')
_DIR = {'I/O': 'bidirectional', 'I': 'input', 'O': 'output', '-': 'passive'}


def eletrico(n):
    nome, dirr = PINAGEM[n]
    if nome in ('GND', 'VCC', 'VCC_IO', 'VBUS'):
        return 'power_in'
    return _DIR.get(dirr, 'unspecified')


def nomes(ini, fim):
    return '[' + ', '.join(f'"{PINAGEM[n][0]}"' for n in range(ini, fim + 1)) + ']'


def tipo_unico(ini, fim):
    ts = {eletrico(n) for n in range(ini, fim + 1)}
    return ts.pop() if len(ts) == 1 else None


# dy do datasheet cresce PARA CIMA; no KiCad Y cresce para baixo -> negar.
def bloco(rot, ini, fim, x0, dy0, dx, ddy, w, h, cota):
    n = fim - ini + 1
    L = [f'  # --- {rot}  ({cota})',
         f'  - nome: {rot}',
         f'    numero_inicial: {ini}',
         f'    n: {n}',
         f'    inicio: {{x: {x0:g}, y: {-dy0:g}}}']
    if n > 1:
        L.append(f'    passo:  {{x: {dx:g}, y: {-ddy:g}}}')
    L.append(f'    tamanho: {{largura: {w:g}, altura: {h:g}}}')
    t = tipo_unico(ini, fim)
    if t:
        L.append(f'    tipo_eletrico: {t}')
    L.append(f'    nomes: {nomes(ini, fim)}')
    L.append('')
    return L


out = []
out.append('# =============================================================================')
out.append('# u-blox NINA-B406-00B — LGA-71 (15,00 x 10,00 x 2,23 mm)')
out.append('# Bluetooth LE com antena de trilha integrada no modulo.')
out.append('#')
out.append('# Datasheet: UBX-19049405 R09 — Table 22 (Land pattern dimensions).')
out.append('# Cada bloco abaixo espelha UMA linha da Table 22: as cotas entram como os')
out.append('# proprios numeros do datasheet (H, F, R, M, N, Q, S, T, U, K, L, P, ZA1,')
out.append('# ZA2, ZB), nao como coordenadas ja calculadas.')
out.append('#')
out.append('# origem: pino_1 -> as posicoes sao relativas ao PINO 1, como o datasheet')
out.append('# cota. `da_borda` traz D e E (borda -> centro do pino 1); o gerador faz a')
out.append('# conversao para o centro do corpo.')
out.append('#')
out.append('# Y segue a convencao do KiCad (cresce para BAIXO). O datasheet cota para')
out.append('# cima, entao os dy aparecem negados aqui.')
out.append('#')
out.append('# Pads sao ORIENTADOS: J (1,15 = "pin length") entra PERPENDICULAR a borda;')
out.append('# I (0,70 = "pin width") corre AO LONGO dela. Fileira em X -> (I, J);')
out.append('# fileira em Y -> (J, I). Trocar isso poe os pads laterais em curto.')
out.append('# =============================================================================')
out.append('')
out.append('nome: "NINA_B406"')
out.append('padrao: custom')
out.append('')
out.append('origem:')
out.append('  referencia: pino_1')
out.append(f'  da_borda: {{esquerda: {D:g}, base: {E:g}}}   # Table 22 D e E')
out.append('')
out.append('corpo:')
out.append(f'  largura: {A:g}          # Table 22 A')
out.append(f'  comprimento: {B:g}      # Table 22 B')
out.append('  formato: retangulo')
out.append('')
out.append('margens:')
out.append('  courtyard: 0.25')
out.append('  silkscreen: 0.12')
out.append('  fab_line: 0.10')
out.append('')
out.append('kicad:')
out.append('  referencia: "U?"')
out.append('  valor: "NINA-B406"')
out.append('  descricao: "u-blox NINA-B406 Bluetooth LE module, LGA-71, 15x10x2.23mm, integrated antenna"')
out.append('  tags: "u-blox nina b406 bluetooth ble lga71 module antenna"')
out.append('')
out.append('grupos_pads:')

# 1..10 lateral inferior — corre em X
out += bloco('lateral_inferior', 1, 10, 0.0, 0.0, H, 0.0, I, J, 'pino 1 na origem; pitch H; pad I x J')
# 11..15 antena — corre em Y
out += bloco('fileira_antena', 11, 15, R, F, 0.0, H, J, I, 'dx=R; de F, pitch H')
# 16..25 lateral superior — dx decrescente
out += bloco('lateral_superior', 16, 25, 9 * H, VS, -H, 0.0, I, J, 'dy=B-2E; pitch H, dx decrescente')
# 26..30 coluna esquerda — dy decrescente
out += bloco('coluna_esquerda', 26, 30, Y, F + 4 * H, 0.0, -H, J, I, 'dx=Y; de F+4H, pitch -H')
# 31..36 interna inferior
out += bloco('interna_inferior', 31, 36, M, N, Q, 0.0, O, O, 'dy=N; de M, pitch Q; pad O')
# 37..42 interna superior — dx decrescente
out += bloco('interna_superior', 37, 42, M + 5 * Q, VS - N, -Q, 0.0, O, O, 'dy=(B-2E)-N; pitch Q')
# 43..46 interna coluna esquerda — dy decrescente
out += bloco('interna_coluna_esq', 43, 46, M, N + 4 * Q, 0.0, -Q, O, O, 'dx=M; de N+4Q, pitch -Q')
# 47..55 externa — dy decrescente
out += bloco('externa', 47, 55, -U, T + 8 * S, 0.0, -S, O, O, 'dx=-U; de T+8S, pitch -S')

# 56..67 central — 4 colunas (grade K-3P..K x L..L+3P, faltando 4 posicoes)
col = [K - 3 * P, K - 2 * P, K - P, K]
out += bloco('central_col1', 56, 57, col[0], L + P, 0.0, P, O, O, 'dx=K-3P; de L+P, pitch P')
out += bloco('central_col2', 58, 61, col[1], L, 0.0, P, O, O, 'dx=K-2P; de L, pitch P')
out += bloco('central_col3', 62, 63, col[2], L + P, 0.0, P, O, O, 'dx=K-P; de L+P, pitch P')
out += bloco('central_col4', 64, 67, col[3], L, 0.0, P, O, O, 'dx=K; de L, pitch P')

# 68..71 GND da antena — 2 corridas de 2
out += bloco('gnd_antena_inferior', 68, 69, ZA1, -ZB, ZA2 - ZA1, 0.0, ZL, ZL, 'dx=ZA1->ZA2; dy=-ZB')
out += bloco('gnd_antena_superior', 70, 71, ZA2, VS + ZB, -(ZA2 - ZA1), 0.0, ZL, ZL, 'dx=ZA2->ZA1; dy=(B-2E)+ZB')

destino = sys.argv[1]
with open(destino, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(out).rstrip() + '\n')

n_blocos = sum(1 for l in out if l.startswith('  - nome:'))
print(f'YAML escrito: {destino}')
print(f'  {n_blocos} blocos  (antes: 71 pads explicitos)')
print(f'  {len(open(destino, encoding="utf-8").readlines())} linhas')
