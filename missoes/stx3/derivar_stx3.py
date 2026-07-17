"""Deriva os 32 pads do Globalstar STX3 e emite modulos_config/Stx3.yaml.

FONTE — STX3 User Manual 8545-0198-01 R-4 (datasheets/STX3.pdf):
  Fig. 1   modulo 0.810 x 1.130 x 0.162 pol  (em TEXTO, nao medido)
  Fig. 7   land pattern recomendado, cotas em POLEGADAS
  Fig. 8   arranjo e numeracao dos pinos
  Table 3  nomes e tipos dos 32 pinos (texto extraido)

O DATUM (o que travava): a Fig.7 e raster e suas cotas medem a partir de linhas
de referencia. O fechamento resolve, e so' fecha de um jeito:

    horizontal: .075 + 6x.100 + .075 = .750   (linha do topo)
                .055 + (.100+.100+.100+.120+.120+.100) + .055 = .750  (base)
                -> concordam
    vertical:   .117 + 8x.100 + .153 = 1.070

    modulo .810 x 1.130  ->  .810-.750 = .060   e   1.130-1.070 = .060
                         ->  .030/lado NOS DOIS EIXOS

O mesmo recuo de .030 em ambos os eixos e' o que prova a leitura: as linhas de
referencia da Fig.7 sao as CENTERLINES dos pads, .030 pol para dentro de cada
borda do modulo. Nenhuma cota foi medida na figura — so' lidas.

RESSALVA HONESTA: o datum ABSOLUTO (campo de pads vs. contorno do modulo) e'
deduzido desse fechamento, nao lido de uma cota. As posicoes RELATIVAS entre
pads — que sao o que solda no modulo — sao todas cotadas.

Uso:  python missoes/stx3/derivar_stx3.py [caminho_do_yaml]
"""
import sys
from pathlib import Path

IN = 25.4                       # polegada -> mm

# ─── Fig. 1 ───
MOD_W, MOD_H = 0.810, 1.130     # modulo, polegadas
ALT_3D = 0.162

# ─── Fig. 7 (polegadas) ───
PITCH = 0.100                   # lados, topo e a maior parte da base
PITCH_RF = 0.120                # folga extra em volta do RFOUT (pino 14)
PAD_CURTO = 0.076               # ao longo da borda
PAD_LONGO = 0.080               # perpendicular a borda (entra no PCB)
TOPO_ATE_COL = 0.117            # centerline do topo -> centro do 1o pad da coluna
COL_ATE_BASE = 0.153            # centro do ultimo pad da coluna -> centerline da base
RECUO = 0.030                   # centerline dos pads para dentro da borda (derivado)

# Centerlines das fileiras/colunas, simetricas em torno do centro do modulo.
X_COL = MOD_W / 2 - RECUO       # 0.375  -> colunas em -+0.375  (vao 0.750 ✓)
Y_ROW = MOD_H / 2 - RECUO       # 0.535  -> fileiras em -+0.535 (vao 1.070 ✓)

# ─── Table 3 + Fig. 8 — sentido anti-horario a partir do pino 1 ───
# Fig.8 mostra CTS(1) no ALTO da coluna esquerda. Y do KiCad cresce para baixo.
ESQ = ["CTS", "RTS", "RESERVED", "NC", "NC", "RESERVED", "VRF", "GND", "GND"]              # 1-9   topo->base
BASE = ["GND", "GND", "GND", "GND", "RFOUT", "GND", "GND"]                                  # 10-16 esq->dir
DIR = ["GND", "GND", "GND", "GND", "RESERVED", "RESERVED", "RESERVED", "PWR_EN", "NC"]      # 17-25 base->topo
TOPO = ["TxD", "RxD", "TEST2", "TEST1", "RESERVED", "RESET", "VDIG"]                        # 26-32 dir->esq

# NC/RESERVED -> passive: o schema nao tem "unconnected"; a Table 3 diz
# "Do NOT connect" para os dois.
TIPO = {"GND": "power_in", "VRF": "power_in", "VDIG": "power_in",
        "RFOUT": "output", "CTS": "output", "RTS": "input", "RESET": "input",
        "PWR_EN": "input", "RxD": "input", "TxD": "output",
        "TEST1": "input", "TEST2": "input", "NC": "passive", "RESERVED": "passive"}

pads = {}   # numero -> (x_mm, y_mm, w_mm, h_mm, nome)


def add(n, nome, x_pol, y_pol, w_pol, h_pol):
    pads[n] = (round(x_pol * IN, 4), round(y_pol * IN, 4),
               round(w_pol * IN, 4), round(h_pol * IN, 4), nome)


# Colunas: 9 pads. O 1o fica .117 abaixo da centerline do topo; pitch .100.
# (Nao sao centradas em y=0 — .117 != .153, entao a coluna e' assimetrica de
#  proposito. Quem centra a coluna desloca o campo inteiro em .018 pol.)
col_y = [(-Y_ROW + TOPO_ATE_COL) + i * PITCH for i in range(9)]
assert abs((col_y[-1] + COL_ATE_BASE) - Y_ROW) < 1e-9, "vertical nao fecha"

# Pads das COLUNAS correm em Y -> o lado longo entra em X: (w,h) = (LONGO, CURTO)
for i, nome in enumerate(ESQ):                      # 1-9: topo -> base
    add(1 + i, nome, -X_COL, col_y[i], PAD_LONGO, PAD_CURTO)
for i, nome in enumerate(DIR):                      # 17-25: base -> topo
    add(17 + i, nome, X_COL, col_y[8 - i], PAD_LONGO, PAD_CURTO)

# Base: 7 pads, pitch IRREGULAR (.120 cerca o RFOUT), centrada entre as colunas.
passos = [PITCH, PITCH, PITCH, PITCH_RF, PITCH_RF, PITCH]
xs = [0.0]
for p in passos:
    xs.append(xs[-1] + p)
xs = [x - xs[-1] / 2 for x in xs]                   # centrar
assert abs(xs[0] + X_COL - 0.055) < 1e-9, "base nao fecha com .055"
# Pads das FILEIRAS correm em X -> o lado longo entra em Y: (w,h) = (CURTO, LONGO)
for i, nome in enumerate(BASE):                     # 10-16: esq -> dir
    add(10 + i, nome, xs[i], Y_ROW, PAD_CURTO, PAD_LONGO)

# Topo: 7 pads, pitch .100 uniforme, centrado.
xs_topo = [(-(6 * PITCH) / 2) + i * PITCH for i in range(7)]
assert abs(xs_topo[0] + X_COL - 0.075) < 1e-9, "topo nao fecha com .075"
for i, nome in enumerate(TOPO):                     # 26-32: dir -> esq
    add(26 + i, nome, xs_topo[6 - i], -Y_ROW, PAD_CURTO, PAD_LONGO)

assert len(pads) == 32, f"esperado 32 pads, derivou {len(pads)}"


def emitir(destino):
    L = []
    L.append('# =============================================================================')
    L.append('# Globalstar STX3 — transmissor satelital simplex, 32 pinos castelados')
    L.append('# Modulo 20,574 x 28,702 x 4,115 mm (0.810 x 1.130 x 0.162 pol)')
    L.append('#')
    L.append('# Datasheet: STX3 User Manual 8545-0198-01 R-4.')
    L.append('# As 32 posicoes sao DERIVADAS das cotas da Fig.7 — nenhuma medida na')
    L.append('# figura. Ver missoes/stx3/derivar_stx3.py para a derivacao e o datum.')
    L.append('#')
    L.append('# padrao: custom porque a fileira INFERIOR tem pitch NAO-UNIFORME')
    L.append('#   .055 | .100 | .100 | .100 | .120 | .120 | .100 | .055')
    L.append('# Os .120 cercam o pino 14 (RFOUT) — folga extra para o RF. O quad_smd')
    L.append('# aplica um pitch so\', entao nao expressa esta peca.')
    L.append('#')
    L.append('# Pads sao ORIENTADOS: o lado longo (.080) entra perpendicular a borda que')
    L.append('# o pad ocupa; o curto (.076) corre ao longo dela. Colunas -> (.080, .076);')
    L.append('# fileiras -> (.076, .080). Trocar isso poe pads em curto.')
    L.append('# =============================================================================')
    L.append('')
    L.append('nome: "Globalstar_STX3"')
    L.append('padrao: custom')
    L.append('fabricante: "Globalstar"')
    L.append('mpn: "~"  # Confidencial')
    L.append('datasheet_url: "~"  # STX3 User Manual 8545-0198-01 R-4')
    L.append('')
    L.append('corpo:')
    L.append(f'  largura: {round(MOD_W * IN, 3)}      # Fig.1: 0.810 pol')
    L.append(f'  comprimento: {round(MOD_H * IN, 3)}  # Fig.1: 1.130 pol')
    L.append(f'  altura_3d: {round(ALT_3D * IN, 3)}   # Fig.1: 0.162 pol')
    L.append('  formato: retangulo')
    L.append('')
    L.append('margens:')
    L.append('  courtyard: 0.5')
    L.append('  silkscreen: 0.12')
    L.append('  fab_line: 0.10')
    L.append('')
    L.append('kicad:')
    L.append('  referencia: "U?"')
    L.append('  valor: "STX3"')
    L.append('  descricao: "Globalstar STX3 simplex satellite transmitter, 32 castellated pads, 20.57x28.70x4.12mm"')
    L.append('  tags: "globalstar stx3 satellite simplex transmitter module castellated"')
    L.append('')
    L.append('pads:')
    grupos = [(1, 9, 'Coluna esquerda (topo->base) — x=-(W/2-.030); 1o pad .117 abaixo da centerline do topo; pitch .100'),
              (10, 16, 'Base (esq->dir) — y=+(H/2-.030); pitch IRREGULAR .100/.100/.100/.120/.120/.100 (RFOUT=14)'),
              (17, 25, 'Coluna direita (base->topo) — x=+(W/2-.030); mesmos Y da coluna esquerda'),
              (26, 32, 'Topo (dir->esq) — y=-(H/2-.030); pitch .100 uniforme')]
    for ini, fim, com in grupos:
        L.append(f'  # --- {com}')
        for n in range(ini, fim + 1):
            x, y, w, h, nome = pads[n]
            L.append(f'  - {{numero: {n}, nome: "{nome}", tipo_eletrico: {TIPO.get(nome, "passive")}, '
                     f'x: {x:g}, y: {y:g}, largura: {w:g}, altura: {h:g}, '
                     f'formato: retangulo, montagem: smd}}')
        L.append('')
    Path(destino).write_text('\n'.join(L).rstrip() + '\n', encoding='utf-8', newline='\n')
    print(f'YAML escrito: {destino} ({len(pads)} pads)')


if __name__ == '__main__':
    destino = sys.argv[1] if len(sys.argv) > 1 else 'modulos_config/Stx3.yaml'
    ys = [p[1] for p in pads.values()]
    xs_ = [p[0] for p in pads.values()]
    print(f'campo de pads: X [{min(xs_):+.3f} .. {max(xs_):+.3f}]  '
          f'Y [{min(ys):+.3f} .. {max(ys):+.3f}] mm')
    print(f'pino 1 (CTS)  : ({pads[1][0]:+.3f}, {pads[1][1]:+.3f})')
    print(f'pino 14 (RFOUT): ({pads[14][0]:+.3f}, {pads[14][1]:+.3f})')
    emitir(destino)
