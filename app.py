#importacion y configuracion de flask
from flask import Flask, render_template, request, session, redirect
import random
from pymongo import MongoClient
from dotenv import load_dotenv
import os
app = Flask (__name__)
app.secret_key = "clave-juego-ahorcado"

categorias = {
    "comidas": ["CHAMPIÑONES","CHOCOLATADA","HAMBURGUESA","SALCHIPAPAS","LANGOSTINOS"],
    "industrial": ["INFORMATICA","EXPO TECNICA", "CONSTRUCCIONES", "ELECTROMECANICA","ESTUDIANTINA"],
    "peliculas": ["RATATOUILLE","INTERSTELAR","BEETLEJUICE","TRANSFORMERS","RAPIDOS Y FURIOSOS"],
    "videojuegos": ["MINECRAFTS","FORTNITE","CALL OF DUTY"],
    "aplicaciones": ["INSTAGRAMS","WHATSAPPS","FACEBOOKS","SPOTIFY"]
}


    #clase palabra
    #administra la palabra secreta y las letras

class Palabra: 
    def __init__(self,palabra):
        self.palabra = palabra.upper()
        self.letras_correctas = []
    def adivinar(self, letra):
            letra = letra.upper()
            if letra in self.palabra:
                if letra not in self.letras_correctas:
                    self.letras_correctas.append(letra)
                return True
            return False
    def mostrar_palabra(self):
        resultado = []
        for letra in self.palabra:
            if letra == " ":
                resultado.append(" ")

            elif letra in self.letras_correctas:
                resultado.append(letra)
            else:
                    resultado.append("_")
        return "".join(resultado)

#clase ahorcado
#administra los intentos y las letras usadas

class Ahorcado:
    def __init__(self,palabra):
        self.palabra = palabra
        self.intentos_restantes = 8
        self.letras_intentadas = []
    #comprueba si la letra elegida esta en la palabra

    def comprobar_letra(self, letra):
        letra = letra.upper()
        if letra in self.letras_intentadas:
             return "repetida"
        self.letras_intentadas.append(letra)
        if letra in self.palabra.palabra:
            self.palabra.adivinar(letra)
            return True
        else:
            self.intentos_restantes -= 1
            return False 
    def gano(self):
      palabra_mostrada = self.palabra.mostrar_palabra()
      if "_" not in palabra_mostrada:
        return True
      
      return False
    def perdio(self):
        if self.intentos_restantes <= 0:
            return True

        return False
    def partida_terminada(self):
        if self.gano() or self.perdio(): 
            return True
        return False   


#ruta principal
#comprueba que flask pueda mostrar una pagina
@app.route("/", methods=["GET","POST"])
def inicio():
    if request.method =="POST":
        jugador = request.form.get("jugador", "").strip()
        if jugador and len(jugador)<=20:
            #limpiamos la sesion del jugador anterior
            session.clear()
            #guardamos el nuevo jugador 
            session["jugador"] = jugador
            session["puntaje_total"] = 0
            return redirect("/categorias")
    return render_template("index.html")

@app.route("/categorias")
def elegir_categoria():
    return render_template("categorias.html")


# Página donde se desarrolla la partida.
@app.route("/jugar/<categoria>", methods=["GET","POST"])
def jugar(categoria):
    if categoria not in categorias:
        return redirect("/categorias")

    if "puntaje_total" not in session:
        session["puntaje_total"] = 0

    if "categoria" not in session or session["categoria"] != categoria:
        session["categoria"] = categoria
        session["palabra"] = random.choice(categorias[categoria])
        session["letras_correctas"] = []
        session["letras_intentadas"] = []
        session["intentos"] = 8 
        session["puntos_partida"]= 0
        session["puntos_otorgados"]= False
        session["resultado_guardado"]= False
    

    mi_palabra = Palabra(session["palabra"])
    mi_palabra.letras_correctas = session["letras_correctas"]

    mi_partida= Ahorcado(mi_palabra)
    mi_partida.letras_intentadas = session["letras_intentadas"]
    mi_partida.intentos_restantes= session["intentos"]

    if request.method == "POST":
        letra = request.form.get("letra", "").upper()

        if len(letra) == 1 and letra.isalpha():
            if not mi_partida.partida_terminada():
                mi_partida.comprobar_letra(letra)

        
        session["letras_correctas"] = mi_palabra.letras_correctas
        session["letras_intentadas"] = mi_partida.letras_intentadas
        session["intentos"] = mi_partida.intentos_restantes

    mensaje = ""

    if mi_partida.gano():
        mensaje = "¡Felicidades! ¡Adivinaste la palabra!"
        if not session["puntos_otorgados"]:
            puntos = 100 + (mi_partida.intentos_restantes * 10)
            session["puntos_partida"]= puntos
            session["puntaje_total"] += puntos
            session["puntos_otorgados"] = True  
            
    elif mi_partida.perdio():
        mensaje = "¡Se terminaron los intentos!"

#guardamos el resultado cuando termina la partida
    if mi_partida.partida_terminada():
        if not session["resultado_guardado"]:
            resultado= { "jugador": session.get("jugador","invitado"),
            "categoria": categoria,
            "resultado": "victoria"if mi_partida.gano() else "derrota",
            "puntos": session["puntos_partida"]
            }
            try:
                partidas.insert_one(resultado)
                session["resultado_guardado"]= True
                print ("¡resultado guardado en MongoDB!")
            except Exception as e:
                    print("error al guardar el resultado:", e)
    errores = 8 -  session["intentos"]
    # Mostramos la página con los datos actualizados.
    return render_template(
        "juego.html",
        palabra_mostrada=mi_palabra.mostrar_palabra(),
        intentos=mi_partida.intentos_restantes,
        mensaje=mensaje,
        letras_intentadas=mi_partida.letras_intentadas,
        puntos_partida=session["puntos_partida"],
        puntaje_total=session["puntaje_total"],
        jugador=session.get("jugador"),
        categoria=categoria,
        errores=errores
    )
@app.route("/reiniciar")
def reiniciar():
    categoria = session.get("categoria")
    jugador = session.get("jugador")
    puntaje_total = session.get("puntaje_total", 0)

    #prueba temporal
    print("antes de reiniciar:", jugador, puntaje_total)
    session.clear()
#recuperacion de datos del jugador
    session["jugador"] = jugador
    session["puntaje_total"] = puntaje_total
    #prueba temporal
    print("despues de reiniciar:", session.get("jugador"), session.get("puntaje_total"))
    if categoria:
        return redirect(f"/jugar/{categoria}")
    return redirect("/categorias")

#cargamos las variables de archivo .env
load_dotenv()

#obtenemos la direccion de conexion
MONGO_URI= os.getenv("MONGO_URI")

#CREAMOS LA CONEXION CON MONGODB
cliente = MongoClient(MONGO_URI)

#seleccionamos nuestra base de datos
db = cliente["ahorcado"]

#seleccionamos la coleccion de partidas
partidas= db["partidas"]

#prueba temporal
try:
    cliente.admin.command("ping")
    print("Conexión exitosa a MongoDB")
except Exception as e:
    print("Error al conectar a MongoDB:", e)

#ranking general 
@app.route("/ranking")
def ranking():
    resultados = list(partidas.aggregate([
        {
            "$group":{"_id":"$jugador",
            "puntos_totales":{"$sum":"$puntos"}
            }
        },
        {
            "$sort":{"puntos_totales":-1}
        }
    ]))
    return render_template("ranking.html", resultados=resultados)  
#inicio del servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))