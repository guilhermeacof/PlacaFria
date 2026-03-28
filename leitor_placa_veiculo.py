import argparse
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


PLACA_RE = re.compile(r"^(?:[A-Z]{3}[0-9]{4}|[A-Z]{3}[0-9][A-Z][0-9]{2})$")


@dataclass
class ResultadoConsulta:
    sucesso: bool
    fonte: str
    placa_consultada: str
    placa_retorno: Optional[str] = None
    marca_modelo: Optional[str] = None
    cor: Optional[str] = None
    ano_fabricacao_modelo: Optional[str] = None
    chassi: Optional[str] = None
    erro: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "sucesso": self.sucesso,
            "fonte": self.fonte,
            "placa_consultada": self.placa_consultada,
            "placa_retorno": self.placa_retorno,
            "marca_modelo": self.marca_modelo,
            "cor": self.cor,
            "ano_fabricacao_modelo": self.ano_fabricacao_modelo,
            "chassi": self.chassi,
            "erro": self.erro,
        }


class DependenciaAusenteError(RuntimeError):
    pass


class ConsultaLupaVeicular:
    def __init__(self, headless: bool = True) -> None:
        self.headless = headless

    @staticmethod
    def normalizar_placa(placa: str) -> str:
        placa_limpa = re.sub(r"[^A-Za-z0-9]", "", placa.upper().strip())
        if not PLACA_RE.fullmatch(placa_limpa):
            raise ValueError("Placa inválida. Use formato ABC1234 ou ABC1D23.")
        return placa_limpa

    @staticmethod
    def formatar_placa_para_input(placa: str) -> str:
        return placa

    @staticmethod
    def _mensagem_instalacao_playwright() -> str:
        return (
            "Dependência ausente: playwright. Instale com: "
            "pip install playwright && playwright install"
        )

    @staticmethod
    def _importar_playwright():
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
        except ModuleNotFoundError as exc:
            raise DependenciaAusenteError(ConsultaLupaVeicular._mensagem_instalacao_playwright()) from exc
        return sync_playwright, PlaywrightTimeoutError

    @staticmethod
    def _extrair_texto_irmao(page, rotulo: str) -> Optional[str]:
        script = """
        (rotulo) => {
            const normalizar = (texto) => (texto || '').replace(/\s+/g, ' ').trim().toUpperCase();
            const elementos = Array.from(document.querySelectorAll('body *'));
            const alvo = elementos.find(el => normalizar(el.textContent) === normalizar(rotulo));
            if (!alvo) return null;

            const containers = [];
            if (alvo.parentElement) containers.push(alvo.parentElement);
            if (alvo.parentElement && alvo.parentElement.parentElement) {
                containers.push(alvo.parentElement.parentElement);
            }

            for (const container of containers) {
                const textos = Array.from(container.querySelectorAll('*'))
                    .map(el => (el.textContent || '').replace(/\s+/g, ' ').trim())
                    .filter(Boolean)
                    .filter(t => t.toUpperCase() !== rotulo.toUpperCase());
                if (textos.length) return textos[0];
            }
            return null;
        }
        """
        return page.evaluate(script, rotulo)

    @staticmethod
    def _extrair_linha_topo(texto_pagina: str) -> Optional[str]:
        for linha in texto_pagina.splitlines():
            linha = linha.strip()
            if re.search(r"[A-Z]/.+", linha):
                return linha
        return None

    def consultar(self, placa: str) -> Dict[str, Optional[str]]:
        placa_normalizada = self.normalizar_placa(placa)

        try:
            sync_playwright, PlaywrightTimeoutError = self._importar_playwright()
        except DependenciaAusenteError as exc:
            return ResultadoConsulta(
                sucesso=False,
                fonte="lupaveicular.com",
                placa_consultada=placa_normalizada,
                erro=str(exc),
            ).to_dict()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page(viewport={"width": 1440, "height": 1200})

            try:
                page.goto("https://www.lupaveicular.com/", wait_until="domcontentloaded", timeout=60000)

                try:
                    page.get_by_text("Prosseguir", exact=True).click(timeout=3000)
                except PlaywrightTimeoutError:
                    pass

                input_placa = page.locator("#plate")
                input_placa.wait_for(state="visible", timeout=15000)
                input_placa.click()
                input_placa.fill(self.formatar_placa_para_input(placa_normalizada))

                page.get_by_role("button", name=re.compile("consultar", re.I)).click()

                page.wait_for_load_state("networkidle", timeout=30000)
                page.get_by_text("Dados da Consulta", exact=True).wait_for(timeout=20000)

                marca_modelo = self._extrair_texto_irmao(page, "MARCA/MODELO")
                placa_resultado = self._extrair_texto_irmao(page, "PLACA")
                cor = self._extrair_texto_irmao(page, "COR")
                ano = self._extrair_texto_irmao(page, "ANO FABRICAÇÃO/MODELO")
                chassi = self._extrair_texto_irmao(page, "CHASSI")

                if not marca_modelo:
                    try:
                        texto_topo = page.locator("body").inner_text()
                        marca_modelo = self._extrair_linha_topo(texto_topo)
                    except Exception:
                        marca_modelo = None

                return ResultadoConsulta(
                    sucesso=True,
                    fonte="lupaveicular.com",
                    placa_consultada=placa_normalizada,
                    placa_retorno=placa_resultado,
                    marca_modelo=marca_modelo,
                    cor=cor,
                    ano_fabricacao_modelo=ano,
                    chassi=chassi,
                ).to_dict()
            except Exception as exc:
                return ResultadoConsulta(
                    sucesso=False,
                    fonte="lupaveicular.com",
                    placa_consultada=placa_normalizada,
                    erro=str(exc),
                ).to_dict()
            finally:
                browser.close()


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Consulta uma placa no site Lupa Veicular e extrai os dados visíveis da página."
    )
    parser.add_argument(
        "placa",
        nargs="?",
        help="Placa no formato ABC1234 ou ABC1D23",
    )
    parser.add_argument(
        "--mostrar-navegador",
        action="store_true",
        help="Abre o navegador visível",
    )
    return parser


USO_EXEMPLO = "Exemplo de uso: python leitor_placa_veiculo.py ABC1234"


def executar_cli(argv: Optional[List[str]] = None) -> int:
    parser = criar_parser()
    args = parser.parse_args(argv)

    if not args.placa:
        parser.print_help()
        print(f"\n{USO_EXEMPLO}")
        return 0

    try:
        consulta = ConsultaLupaVeicular(headless=not args.mostrar_navegador)
        resultado = consulta.consultar(args.placa)
    except ValueError as exc:
        print(json.dumps({"sucesso": False, "erro": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if resultado.get("sucesso") else 1


def main(argv: Optional[List[str]] = None) -> int:
    return executar_cli(argv)


if __name__ == "__main__":
    main()


# ----------------------------
# Testes
# Execute com: python -m unittest leitor_placa_veiculo.py
# ----------------------------

import io
import unittest
from contextlib import redirect_stdout


class TestConsultaLupaVeicular(unittest.TestCase):
    def test_normalizar_placa_antiga(self):
        self.assertEqual(ConsultaLupaVeicular.normalizar_placa("abc-1234"), "ABC1234")

    def test_normalizar_placa_mercosul(self):
        self.assertEqual(ConsultaLupaVeicular.normalizar_placa("bra2e19"), "BRA2E19")

    def test_normalizar_placa_invalida(self):
        with self.assertRaises(ValueError):
            ConsultaLupaVeicular.normalizar_placa("12")

    def test_formatar_placa_para_input_mantem_valor(self):
        self.assertEqual(ConsultaLupaVeicular.formatar_placa_para_input("ABC1234"), "ABC1234")

    def test_extrair_linha_topo(self):
        texto = """
        CONSULTAR PLACA
        I/BMW 535I FR71
        DADOS DA CONSULTA
        """
        self.assertEqual(ConsultaLupaVeicular._extrair_linha_topo(texto), "I/BMW 535I FR71")

    def test_extrair_linha_topo_sem_padrao_retorna_none(self):
        texto = "CONSULTAR PLACA\nDADOS DA CONSULTA\n"
        self.assertIsNone(ConsultaLupaVeicular._extrair_linha_topo(texto))

    def test_resultado_dependencia_ausente_tem_mensagem_util(self):
        original = ConsultaLupaVeicular._importar_playwright
        try:
            ConsultaLupaVeicular._importar_playwright = staticmethod(
                lambda: (_ for _ in ()).throw(DependenciaAusenteError("playwright ausente"))
            )
            consulta = ConsultaLupaVeicular()
            resultado = consulta.consultar("ABC1234")
            self.assertFalse(resultado["sucesso"])
            self.assertEqual(resultado["placa_consultada"], "ABC1234")
            self.assertIn("playwright", resultado["erro"])
        finally:
            ConsultaLupaVeicular._importar_playwright = original

    def test_executar_cli_sem_argumentos_nao_lanca_system_exit_2(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = executar_cli([])
        self.assertEqual(codigo, 0)
        texto = saida.getvalue()
        self.assertIn("usage:", texto)
        self.assertIn("Exemplo de uso:", texto)

    def test_executar_cli_com_placa_invalida_retorna_erro(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = executar_cli(["12"])
        self.assertEqual(codigo, 1)
        texto = saida.getvalue()
        self.assertIn("Placa inválida", texto)

    def test_executar_cli_com_sucesso_retorna_zero(self):
        original = ConsultaLupaVeicular.consultar
        try:
            ConsultaLupaVeicular.consultar = lambda self, placa: {
                "sucesso": True,
                "fonte": "lupaveicular.com",
                "placa_consultada": placa,
            }
            saida = io.StringIO()
            with redirect_stdout(saida):
                codigo = executar_cli(["ABC1234"])
            self.assertEqual(codigo, 0)
            self.assertIn('"placa_consultada": "ABC1234"', saida.getvalue())
        finally:
            ConsultaLupaVeicular.consultar = original

    def test_executar_cli_com_falha_retorna_um(self):
        original = ConsultaLupaVeicular.consultar
        try:
            ConsultaLupaVeicular.consultar = lambda self, placa: {
                "sucesso": False,
                "fonte": "lupaveicular.com",
                "placa_consultada": placa,
                "erro": "falha simulada",
            }
            saida = io.StringIO()
            with redirect_stdout(saida):
                codigo = executar_cli(["ABC1234"])
            self.assertEqual(codigo, 1)
            self.assertIn("falha simulada", saida.getvalue())
        finally:
            ConsultaLupaVeicular.consultar = original

    def test_main_retorna_codigo_sem_system_exit(self):
        original = ConsultaLupaVeicular.consultar
        try:
            ConsultaLupaVeicular.consultar = lambda self, placa: {
                "sucesso": True,
                "fonte": "lupaveicular.com",
                "placa_consultada": placa,
            }
            saida = io.StringIO()
            with redirect_stdout(saida):
                codigo = main(["ABC1234"])
            self.assertEqual(codigo, 0)
            self.assertIn('"sucesso": true', saida.getvalue().lower())
        finally:
            ConsultaLupaVeicular.consultar = original
