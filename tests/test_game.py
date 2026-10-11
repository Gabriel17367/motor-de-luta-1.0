import unittest

import pygame

from nc import (
    AZUL_P1,
    GerenciadorEfeitos,
    Lutador,
    MaquinaEstadosIA,
    VERMELHO_P2,
    tecla_pressionada,
)


CONTROLES = {
    "esquerda": pygame.K_LEFT,
    "direita": pygame.K_RIGHT,
    "pulo": pygame.K_UP,
    "ataque1": pygame.K_KP1,
    "ataque2": pygame.K_KP2,
}


class TestControlesVirtuais(unittest.TestCase):
    def test_le_keycode_maior_que_buffer_de_teclas(self):
        keycode = pygame.K_LEFT

        self.assertTrue(tecla_pressionada({keycode: True}, keycode))
        self.assertFalse(tecla_pressionada({}, keycode))


class TestInteligenciaArtificial(unittest.TestCase):
    def test_se_aproxima_quando_o_alvo_esta_distante(self):
        lutador = Lutador(1, 100, 100, AZUL_P1, CONTROLES)
        alvo = Lutador(2, 500, 100, VERMELHO_P2, CONTROLES)
        ia = MaquinaEstadosIA(CONTROLES)

        comandos = ia.pensar(lutador, alvo)

        self.assertEqual(ia.estado, "APROXIMAR")
        self.assertEqual(comandos, {CONTROLES["direita"]: True})


class TestCombate(unittest.TestCase):
    def setUp(self):
        self.atacante = Lutador(1, 100, 100, AZUL_P1, CONTROLES)
        self.alvo = Lutador(2, 150, 100, VERMELHO_P2, CONTROLES)
        self.efeitos = GerenciadorEfeitos()

    def test_golpe_leve_causa_dano_e_hitstun(self):
        self.atacante.atacar(self.alvo, "leve", self.efeitos)

        self.assertAlmostEqual(self.alvo.vida, 97.5)
        self.assertEqual(self.alvo.hitstun, 20)
        self.assertEqual(self.alvo.contador_combo, 1)

    def test_combo_aplica_scaling_e_pushback_dinamico(self):
        self.atacante.atacar(self.alvo, "leve", self.efeitos)
        primeiro_pushback = self.alvo.knockback_x
        self.atacante.cooldown_ataque = 0

        self.atacante.atacar(self.alvo, "leve", self.efeitos)

        self.assertAlmostEqual(self.alvo.vida, 96.5)
        self.assertEqual(self.alvo.contador_combo, 2)
        self.assertGreater(self.alvo.knockback_x, primeiro_pushback)

    def test_defesa_aplica_chip_e_blockstun(self):
        self.alvo.defendendo = True

        self.atacante.atacar(self.alvo, "pesado", self.efeitos)

        self.assertEqual(self.alvo.vida, 98)
        self.assertEqual(self.alvo.hitstun, 25)
        self.assertEqual(self.alvo.contador_combo, 0)
        self.assertEqual(self.efeitos.hit_stop, 2)


if __name__ == "__main__":
    unittest.main()