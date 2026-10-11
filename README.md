# Motor de Luta 2D

Jogo de luta 2D em Pygame com duas CPUs que combatem automaticamente. Os gráficos e efeitos são desenhados pelo próprio jogo, sem arquivos de mídia externos.

## Executar no desktop

Requer Python 3.10 ou superior.

```powershell
python -m pip install -r requirements.txt
python nc.py
```

## Executar no navegador

O projeto usa Pygbag para compilar o jogo para WebAssembly. Na raiz do projeto:

```powershell
python -m pip install pygbag
python -X utf8 -m pygbag main.py
```

Abra o endereço local informado pelo Pygbag. O navegador precisa acessar a internet para carregar o runtime WebAssembly.