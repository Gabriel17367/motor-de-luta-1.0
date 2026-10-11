<div align="center">

# Motor de Luta 2D

**Uma arena CPU vs CPU construída em Python e Pygame.**

[![CI](https://github.com/Gabriel17367/motor-de-luta-1.0/actions/workflows/ci.yml/badge.svg)](https://github.com/Gabriel17367/motor-de-luta-1.0/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Pygame CE](https://img.shields.io/badge/Pygame--CE-2.5%2B-14A76C)

</div>

Dois lutadores controlados por máquinas de estado entram em combate automaticamente. Física, golpes e efeitos são feitos em código; o projeto não depende de imagens ou áudio externos.

## Destaques

- IA com tempo de reação e decisões baseadas na distância e no cooldown.
- Golpes leves e pesados com dano, hitstun, blockstun, chip damage e pushback.
- Combos com escalonamento de dano e empurrão progressivo.
- Hit stop, tremor de câmera, partículas e animações procedurais.
- Execução desktop com Pygame CE ou no navegador com Pygbag/WebAssembly.

## Começar

Requer Python 3.10 ou superior.

```bash
python -m pip install -r requirements.txt
python nc.py
```

As duas CPUs lutam sem comandos do jogador. Quando a luta termina, pressione **Espaço** para reiniciar.

### Navegador

O Pygbag empacota o jogo para WebAssembly. Execute na raiz do projeto:

```bash
python -m pip install pygbag
python -X utf8 -m pygbag main.py
```

Abra o endereço local exibido pelo Pygbag. O runtime do navegador precisa de acesso à internet.

## Estrutura

| Arquivo | Responsabilidade |
| --- | --- |
| `nc.py` | Lutadores, frame data, IA, física, efeitos, interface e loop do jogo. |
| `main.py` | Ponto de entrada assíncrono para o Pygbag. |
| `tests/test_game.py` | Testes das entradas virtuais, decisões da IA e resolução de golpes. |
| `.github/workflows/ci.yml` | Verificações automáticas em pushes e pull requests. |

## Testes

```bash
python -m unittest discover -s tests -v
```

## Dependências

- [Pygame CE](https://pyga.me/) para desktop e execução WebAssembly.
- [Pygbag](https://pygame-web.github.io/) apenas para compilar e servir a versão de navegador.