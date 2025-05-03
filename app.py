from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/consultar_lote', methods=['POST'])
def consultar_lote():
    billing_ids = request.json.get('billing_ids', [])
    resultados = []

    service = Service("C:/Users/Usuario/Desktop/consulta_clientes_web/chromedriver.exe")  # ajusta si cambia la ruta
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 1. Login una sola vez
        driver.get("http://mira.supercanal.com.ar/users/login")
        time.sleep(1)
        driver.find_element(By.ID, "UserUsername").send_keys("ushuaia")
        driver.find_element(By.ID, "UserPassword").send_keys("utush49i")
        driver.find_element(By.CSS_SELECTOR, "div.submit > input[type='submit']").click()
        time.sleep(2)

        for billing_id in billing_ids:
            try:
                # Ir a Clientes
                driver.find_element(By.CSS_SELECTOR, "#menu > ul > li:nth-child(2) > a").click()
                time.sleep(1)

                # Buscar ID
                input_field = driver.find_element(By.ID, "ClientBillingId")
                input_field.clear()
                input_field.send_keys(billing_id)
                time.sleep(0.5)
                driver.find_element(By.XPATH, "//input[@value='Filtrar']").click()
                time.sleep(1.5)

                # Buscar coincidencia exacta
                encontrado = False
                for i in range(3, 20):
                    try:
                        texto = driver.find_element(By.XPATH, f"//*[@id='filters']/table/tbody/tr[{i}]/td[1]").text.strip()
                        if texto == billing_id:
                            driver.find_element(By.XPATH, f"//*[@id='filters']/table/tbody/tr[{i}]/td[6]/a").click()
                            encontrado = True
                            break
                    except:
                        break

                if not encontrado:
                    resultados.append({"id": billing_id, "estado": "cliente no encontrado", "rx": "-"})
                    continue

                time.sleep(1.5)

                # Buscar FZAN
                filas = driver.find_elements(By.XPATH, "//*[@id='primaryContent']/table[2]/tbody/tr")
                equipo_encontrado = False
                for fila in filas:
                    try:
                        link = fila.find_element(By.CSS_SELECTOR, "td:nth-child(5) > a")
                        link.click()
                        equipo_encontrado = True
                        break
                    except:
                        continue

                if not equipo_encontrado:
                    resultados.append({"id": billing_id, "estado": "sin equipo", "rx": "-"})
                    continue

                time.sleep(1.5)

                # Estado
                estado = driver.find_element(By.CSS_SELECTOR, "#primaryContent img[title]").get_attribute("title")
                rx = "-"
                if estado == "El equipo responde":
                    rx = driver.find_element(By.CSS_SELECTOR, "#primaryContent table:nth-child(6) tr:nth-child(7) td:nth-child(3)").text.strip()

                resultados.append({"id": billing_id, "estado": estado, "rx": rx})

            except Exception as ex:
                print(f"Error con cliente {billing_id}:", ex)
                resultados.append({"id": billing_id, "estado": "error", "rx": "-"})

        driver.quit()
        return jsonify({"resultados": resultados})

    except Exception as e:
        print("Error general:", e)
        driver.quit()
        return jsonify({"resultados": [{"id": id, "estado": "error", "rx": "-"} for id in billing_ids]})

if __name__ == '__main__':
    app.run(debug=True)
