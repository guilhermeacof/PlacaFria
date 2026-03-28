LEITOR DE PLACA VEICULAR — Consulta automática e interface web
============================================================

📌 **Descrição**
Este sistema consulta informações de veículos a partir da placa, automatizando o site https://www.xxxxxxxxxxx.com/.
Inclui interface web com leitura por câmera (OCR) e consulta automática.

---

🚀 **Instalação Rápida no Windows**

1. Baixe e instale o [Python 3.10+](https://www.python.org/downloads/) (marque "Add Python to PATH" na instalação).
2. Baixe/clique duas vezes no arquivo **instalar.bat** OU execute no terminal:
   
       instalar.bat

   Isso irá:
   - Criar ambiente virtual
   - Instalar todas as dependências (Playwright, OCR, câmera)
   - Instalar navegadores Playwright

3. Ative o ambiente virtual e rode o sistema:
   
       venv\Scripts\activate
       python app.py

4. Acesse a interface web em: http://localhost:5000

---

💻 **Instalação Manual (Windows/Linux/Mac)**

1. Instale o Python 3.10+ e o [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (Windows: baixe o instalador e adicione ao PATH).
2. (Opcional) Crie ambiente virtual:
   - Windows:
         python -m venv venv
         venv\Scripts\activate
   - Linux/Mac:
         python3 -m venv venv
         source venv/bin/activate
3. Instale dependências:
       pip install -r requirements-camera.txt
       pip install playwright
       playwright install
4. Rode a interface web:
       python app.py
   Acesse: http://localhost:5000

---

▶️ **Como Usar (linha de comando)**

Consulta simples:
    python leitor_placa_veiculo.py ABC1234

Com navegador visível:
    python leitor_placa_veiculo.py ABC1234 --mostrar-navegador

---

🌐 **Como Usar (interface web)**

1. Execute:
       python app.py
2. Abra o navegador em http://localhost:5000
3. Consulte placas digitando ou usando a câmera (botão "Abrir Câmera" > "Capturar").

---

🧪 **Testes**

Execute os testes automatizados:
    python -m unittest leitor_placa_veiculo.py

---

⚠️ **Observações**

- O programa depende do site Lupa Veicular (pode mudar layout a qualquer momento).
- Alguns dados podem estar ocultos pelo site (pagos).
- O OCR depende da qualidade da imagem e da instalação do Tesseract.
- Uso recomendado apenas para fins legais.

---

💡 **Exemplo de saída**

{
  "sucesso": true,
  "placa_consultada": "ABC1234",
  "marca_modelo": "I/BMW 535I FR71",
  "ano_fabricacao_modelo": "2013/2014"
}

"""
