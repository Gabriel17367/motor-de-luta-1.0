import asyncio
import random

import pygame

# ==========================================
# 1. CONSTANTES E CONFIGURAÇÕES DO MOTOR
# ==========================================
LARGURA_TELA = 1000
ALTURA_TELA = 600
FPS = 60
GRAVIDADE = 1.5

# Paleta de Cores
BRANCO = (255, 255, 255)
PRETO = (15, 15, 18)
CINZA = (100, 100, 100)
VERMELHO_SANGUE = (220, 20, 20)
VERDE_VIDA = (40, 220, 40)
AZUL_P1 = (40, 120, 255)
VERMELHO_P2 = (255, 60, 60)

# ==========================================
# 2. SISTEMA DE EFEITOS (PARTÍCULAS E CAMERA)
# ==========================================
class Particula:
    def __init__(self, x, y, cor, velocidade_x, velocidade_y, tamanho, tempo_vida):
        self.x = x
        self.y = y
        self.cor = cor
        self.vx = velocidade_x
        self.vy = velocidade_y
        self.tamanho = tamanho
        self.tempo_vida = tempo_vida
        self.vida_max = tempo_vida

    def atualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.5 # Gravidade da partícula
        self.tempo_vida -= 1
        # Encolhe a partícula com o tempo
        self.tamanho = max(0, self.tamanho - 0.2)

    def desenhar(self, tela, offset_x, offset_y):
        if self.tempo_vida > 0 and self.tamanho > 0:
            # Pygame não suporta alpha direto em rects básicos, simulamos com tamanho menor
            pygame.draw.rect(tela, self.cor, (self.x + offset_x, self.y + offset_y, self.tamanho, self.tamanho))

class GerenciadorEfeitos:
    def __init__(self):
        self.particulas = []
        self.camera_shake = 0
        self.hit_stop = 0 # Frames onde o jogo congela para dar impacto

    def gerar_hit_spark(self, x, y, tipo):
        qtd = 15 if tipo == 'hit' else 8
        for _ in range(qtd):
            vx = random.uniform(-5, 5)
            vy = random.uniform(-10, 2)
            tamanho = random.uniform(4, 10)
            tempo = random.randint(15, 30)
            
            if tipo == 'hit':
                cor = random.choice([(255, 50, 0), (255, 200, 0), VERMELHO_SANGUE])
            else: # Block
                cor = random.choice([(100, 200, 255), BRANCO, CINZA])
                
            self.particulas.append(Particula(x, y, cor, vx, vy, tamanho, tempo))

    def atualizar(self):
        # Atualiza tela tremendo
        if self.camera_shake > 0:
            self.camera_shake -= 1
            
        # Limpa partículas mortas
        for p in self.particulas[:]:
            p.atualizar()
            if p.tempo_vida <= 0:
                self.particulas.remove(p)

    def get_camera_offset(self):
        if self.camera_shake > 0:
            return random.randint(-5, 5), random.randint(-5, 5)
        return 0, 0

# ==========================================
# 3. MÁQUINA DE ESTADOS DA INTELIGÊNCIA ARTIFICIAL
# ==========================================
class MaquinaEstadosIA:
    def __init__(self, controles):
        self.controles = controles
        self.estado = "IDLE"
        self.timer = 0

    def pensar(self, ia, alvo):
        teclas = {}
        if not ia.vivo:
            return teclas

        distancia = abs(ia.rect.centerx - alvo.rect.centerx)

        if self.timer > 0:
            self.timer -= 1
        else:
            self.timer = random.randint(8, 20)
            if distancia > 115:
                self.estado = "APROXIMAR"
            elif ia.cooldown_ataque == 0 and distancia > 78:
                self.estado = random.choices(
                    ["ATACAR_LEVE", "ATACAR_PESADO", "RECUAR/DEFENDER"],
                    weights=[5, 2, 1],
                    k=1,
                )[0]
            elif ia.cooldown_ataque > 0:
                self.estado = "RECUAR/DEFENDER"
            else:
                self.estado = random.choice(["ATACAR_LEVE", "RECUAR/DEFENDER"])

        # Execução
        if self.estado == "APROXIMAR":
            teclas[self.controles['direita'] if alvo.rect.centerx > ia.rect.centerx else self.controles['esquerda']] = True
        elif self.estado == "RECUAR/DEFENDER":
            teclas[self.controles['esquerda'] if alvo.rect.centerx > ia.rect.centerx else self.controles['direita']] = True
        elif self.estado == "ATACAR_LEVE":
            teclas[self.controles['ataque1']] = True
        elif self.estado == "ATACAR_PESADO":
            teclas[self.controles['ataque2']] = True

        return teclas


def tecla_pressionada(teclas, codigo):
    """Lê tanto o buffer do Pygame quanto o mapa do controle virtual da IA."""
    if isinstance(teclas, dict):
        return teclas.get(codigo, False)
    if codigo < len(teclas):
        return bool(teclas[codigo])
    return False


class SistemaFisica:
    @staticmethod
    def aplicar(lutador, dx, largura_tela, altura_chao):
        lutador.velocidade_y += GRAVIDADE
        dy = lutador.velocidade_y

        if lutador.rect.left + dx < 0:
            dx = -lutador.rect.left
        if lutador.rect.right + dx > largura_tela:
            dx = largura_tela - lutador.rect.right

        if lutador.rect.bottom + dy >= altura_chao:
            lutador.velocidade_y = 0
            lutador.no_chao = True
            dy = altura_chao - lutador.rect.bottom

        lutador.rect.x += dx
        lutador.rect.y += dy

# ==========================================
# 4. A ENTIDADE LUTADOR (Core Physics & Combat)
# ==========================================
class Lutador:
    def __init__(self, id_jogador, x, y, cor, controles):
        self.id = id_jogador
        self.cor = cor
        self.controles = controles
        
        self.rect = pygame.Rect(x, y, 70, 160) 
        self.velocidade_x = 7
        self.velocidade_y = 0
        self.no_chao = True
        self.virado_direita = id_jogador == 1
        
        # Status
        self.vida = 100
        self.vivo = True
        self.atacando = False
        self.defendendo = False
        self.cooldown_ataque = 0
        self.hitstun = 0
        self.knockback_x = 0
        self.contador_combo = 0
        self.golpe_atual = None

        # FRAME DATA (O Coração do Combate)
        self.golpes = {
            'leve': {'cooldown': 15, 'dano': 4, 'hitstun': 20, 'push': 4, 'blockstun': 10, 'chip': 0, 'tamanho': (60, 25), 'cor': BRANCO},
            'pesado': {'cooldown': 40, 'dano': 15, 'hitstun': 45, 'push': 12, 'blockstun': 25, 'chip': 2, 'tamanho': (90, 45), 'cor': (255, 150, 0)}
        }

    def atualizar(self, largura_tela, altura_chao, alvo, teclas, fx_manager):
        if self.vida <= 0:
            self.vivo = False
            return

        dx = 0
        self.defendendo = False

        # --- GESTÃO DE IMPACTO (HITSTUN) ---
        if self.hitstun > 0:
            self.hitstun -= 1
            dx = self.knockback_x
            if self.knockback_x > 0: self.knockback_x -= 0.5
            elif self.knockback_x < 0: self.knockback_x += 0.5
            
            self.atacando = False
            self.cooldown_ataque = 0
            if self.hitstun == 0:
                self.contador_combo = 0 # Fim do combo
        else:
            # --- LÓGICA DE CONTROLE ---
            if not self.atacando:
                if tecla_pressionada(teclas, self.controles['esquerda']):
                    dx = -self.velocidade_x
                    if self.virado_direita: self.defendendo = True
                        
                if tecla_pressionada(teclas, self.controles['direita']):
                    dx = self.velocidade_x
                    if not self.virado_direita: self.defendendo = True
                        
                if tecla_pressionada(teclas, self.controles['pulo']) and self.no_chao:
                    self.velocidade_y = -22
                    self.no_chao = False
                    
                if tecla_pressionada(teclas, self.controles['ataque1']): self.atacar(alvo, 'leve', fx_manager)
                elif tecla_pressionada(teclas, self.controles['ataque2']): self.atacar(alvo, 'pesado', fx_manager)

        # --- FÍSICA E COLISÃO ---
        SistemaFisica.aplicar(self, dx, largura_tela, altura_chao)

        # Auto-Face (se não estiver atacando/apanhando)
        if not self.atacando and self.hitstun == 0:
            self.virado_direita = alvo.rect.centerx > self.rect.centerx

        if self.cooldown_ataque > 0:
            self.cooldown_ataque -= 1
        else:
            self.atacando = False

    def atacar(self, alvo, tipo, fx_manager):
        if self.cooldown_ataque > 0: return
        
        self.atacando = True
        self.golpe_atual = self.golpes[tipo]
        self.cooldown_ataque = self.golpe_atual['cooldown']
        
        largura, altura = self.golpe_atual['tamanho']
        # Cria hitbox à frente do personagem
        hx = self.rect.centerx if self.virado_direita else self.rect.centerx - largura
        hitbox = pygame.Rect(hx, self.rect.y + 30, largura, altura)

        # --- RESOLUÇÃO DO GOLPE ---
        if hitbox.colliderect(alvo.rect):
            ponto_impacto = (hitbox.right if self.virado_direita else hitbox.left, hitbox.centery)
            
            if alvo.defendendo:
                # BLOQUEIO
                alvo.vida -= self.golpe_atual['chip']
                alvo.hitstun = self.golpe_atual['blockstun']
                alvo.contador_combo = 0
                forca = self.golpe_atual['push'] + 3
                fx_manager.gerar_hit_spark(*ponto_impacto, 'block')
                fx_manager.hit_stop = 2 # Congela levemente
            else:
                # ACERTO (HIT)
                alvo.contador_combo += 1
                dano_real = max(self.golpe_atual['dano'] - (alvo.contador_combo * 1.5), 1)
                alvo.vida -= dano_real
                alvo.hitstun = self.golpe_atual['hitstun']
                forca = self.golpe_atual['push'] + (alvo.contador_combo * 2)
                
                fx_manager.gerar_hit_spark(*ponto_impacto, 'hit')
                fx_manager.hit_stop = 4 # Congelamento forte de impacto
                
                if tipo == 'pesado':
                    fx_manager.camera_shake = 10 # Treme a tela em golpe pesado

            alvo.knockback_x = forca if self.virado_direita else -forca

    def desenhar(self, tela, offset_x, offset_y):
        # ANIMAÇÃO PROCEDURAL (O corpo reage ao estado)
        cor_desenho = CINZA if self.defendendo else self.cor
        if self.hitstun > 0 and not self.defendendo:
            cor_desenho = VERMELHO_SANGUE # Pisca vermelho se apanhando

        # Se agacha levemente na defesa
        h_atual = 140 if self.defendendo else 160
        y_atual = self.rect.bottom - h_atual
        corpo = pygame.Rect(self.rect.x + offset_x, y_atual + offset_y, self.rect.width, h_atual)
        
        # Desenha o Corpo
        pygame.draw.rect(tela, cor_desenho, corpo, border_radius=8)

        # Desenha os "Olhos" (Para mostrar direção)
        olho_x = corpo.right - 20 if self.virado_direita else corpo.left + 5
        pygame.draw.rect(tela, BRANCO, (olho_x, corpo.y + 15, 15, 10))

        # Desenha a arma/braço se atacando
        if self.atacando and self.golpe_atual:
            w, h = self.golpe_atual['tamanho']
            bx = corpo.centerx if self.virado_direita else corpo.centerx - w
            braco = pygame.Rect(bx, corpo.y + 30, w, h)
            pygame.draw.rect(tela, self.golpe_atual['cor'], braco, border_radius=4)

# ==========================================
# 5. UI E RENDERIZAÇÃO
# ==========================================
def desenhar_ui(tela, p1, p2, fonte_combo, fonte_sys):
    # Barras de Vida P1
    pygame.draw.rect(tela, BRANCO, (46, 26, 408, 38))
    pygame.draw.rect(tela, VERMELHO_SANGUE, (50, 30, 400, 30))
    pygame.draw.rect(tela, VERDE_VIDA, (50, 30, max(0, p1.vida) * 4, 30))
    
    # Barras de Vida P2 (Alinhada à direita)
    pygame.draw.rect(tela, BRANCO, (546, 26, 408, 38))
    pygame.draw.rect(tela, VERMELHO_SANGUE, (550, 30, 400, 30))
    vida_p2 = max(0, p2.vida) * 4
    pygame.draw.rect(tela, VERDE_VIDA, (550 + (400 - vida_p2), 30, vida_p2, 30))

    # Textos de Combo
    if p1.contador_combo >= 2:
        texto = fonte_combo.render(f"{p1.contador_combo} HITS", True, (255, 200, 0))
        tela.blit(texto, (50, 80))
    if p2.contador_combo >= 2:
        texto = fonte_combo.render(f"{p2.contador_combo} HITS", True, (255, 200, 0))
        tela.blit(texto, (800, 80))

    # Nomes
    tela.blit(fonte_sys.render("MÁQUINA 1", True, BRANCO), (50, 5))
    tela.blit(fonte_sys.render("MÁQUINA 2", True, BRANCO), (800, 5))

# ==========================================
# 6. O LOOP PRINCIPAL (MAIN)
# ==========================================
async def main():
    pygame.init()
    pygame.font.init()
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption("Motor de Luta Sênior - Complete Edition")
    clock = pygame.time.Clock()

    fonte_combo = pygame.font.SysFont('Impact', 48)
    fonte_sys = pygame.font.SysFont('Arial', 18, bold=True)
    fonte_vitoria = pygame.font.SysFont('Impact', 80)

    # Inicia Módulos
    fx_manager = GerenciadorEfeitos()
    
    # Cada IA injeta comandos virtuais nos controles do respectivo lutador.
    controles_p1 = {'esquerda': pygame.K_a, 'direita': pygame.K_d, 'pulo': pygame.K_w, 'ataque1': pygame.K_r, 'ataque2': pygame.K_t}
    controles_p2 = {'esquerda': pygame.K_LEFT, 'direita': pygame.K_RIGHT, 'pulo': pygame.K_UP, 'ataque1': pygame.K_KP1, 'ataque2': pygame.K_KP2}

    def resetar_jogo():
        lutador1 = Lutador(1, 200, 350, AZUL_P1, controles_p1)
        lutador2 = Lutador(2, 700, 350, VERMELHO_P2, controles_p2)
        ia1 = MaquinaEstadosIA(controles_p1)
        ia2 = MaquinaEstadosIA(controles_p2)
        return lutador1, lutador2, ia1, ia2

    p1, p2, ia1, ia2 = resetar_jogo()
    altura_chao = ALTURA_TELA - 40
    game_over = False

    rodando = True
    while rodando:
        clock.tick(FPS)
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            # Restart se o jogo acabou
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE and game_over:
                p1, p2, ia1, ia2 = resetar_jogo()
                game_over = False

        # Se Hit Stop estiver ativo, congela a lógica (O jogo desenha, mas ninguém se move)
        if fx_manager.hit_stop > 0:
            fx_manager.hit_stop -= 1
        elif not game_over:
            teclas_ia1 = ia1.pensar(p1, p2)
            teclas_ia2 = ia2.pensar(p2, p1)

            p1.atualizar(LARGURA_TELA, altura_chao, p2, teclas_ia1, fx_manager)
            p2.atualizar(LARGURA_TELA, altura_chao, p1, teclas_ia2, fx_manager)

            if not p1.vivo or not p2.vivo:
                game_over = True

        fx_manager.atualizar()
        cx, cy = fx_manager.get_camera_offset()

        # --- RENDERIZAÇÃO ---
        tela.fill(PRETO)
        
        # Desenha o Chão (Com câmera offset)
        pygame.draw.rect(tela, (40, 40, 50), (0 + cx, altura_chao + cy, LARGURA_TELA, 40))

        # Desenha Lutadores
        p1.desenhar(tela, cx, cy)
        p2.desenhar(tela, cx, cy)

        # Desenha Partículas
        for p in fx_manager.particulas:
            p.desenhar(tela, cx, cy)

        # UI (Nunca treme com a câmera)
        desenhar_ui(tela, p1, p2, fonte_combo, fonte_sys)

        # Tela de Game Over
        if game_over:
            s = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150)) # Fundo escuro transparente
            tela.blit(s, (0,0))
            
            vencedor = "MÁQUINA 1" if p1.vivo else "MÁQUINA 2"
            txt = fonte_vitoria.render(f"{vencedor} VENCEU!", True, BRANCO)
            tela.blit(txt, (LARGURA_TELA//2 - txt.get_width()//2, ALTURA_TELA//2 - 50))
            
            txt2 = fonte_sys.render("Pressione ESPAÇO para reiniciar", True, BRANCO)
            tela.blit(txt2, (LARGURA_TELA//2 - txt2.get_width()//2, ALTURA_TELA//2 + 50))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())