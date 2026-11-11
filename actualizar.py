# -*- coding: utf-8 -*-
"""Rehace el indice del asistente despues de editar el perfil.

    python actualizar.py              todo, con evaluacion completa
    python actualizar.py --rapido     sin el juez LLM (mas barato)
    python actualizar.py --sin-evals  solo reconstruye

La cadena tiene seis eslabones y saltarse uno NO da error: el sitio
seguiria respondiendo con la informacion vieja sin avisar. Por eso existe
este archivo, para que no haya que acordarse de los seis.

    perfil/*.md  ->  data/  ->  indice  ->  evals  ->  motor del portafolio
                                                   ->  indice en S3 (Lambda)

Hubo un tiempo en que decia cinco, y el sexto eslabon no existia. El
indice llegaba a Vercel pero nunca a S3, asi que Lambda seguia
respondiendo con el perfil viejo y el proceso terminaba en verde. Un
eslabon que falta en silencio es peor que uno que revienta.

Lo unico que se edita a mano es perfil/. Todo lo demas se regenera, y
cualquier cambio hecho directamente en data/ o en Porfolio/api/ se pierde
en la siguiente ejecucion.
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

# La consola de Windows arranca en cp1252, que no sabe escribir una flecha
# ni una tilde. Cualquier print con un caracter fuera de ese juego mata el
# subproceso con UnicodeEncodeError, y el paso se reporta como fallo
# aunque el trabajo haya salido bien. Pasarle utf-8 a los hijos lo evita
# sin tocar cada script por separado.
ENTORNO = dict(os.environ, PYTHONIOENCODING="utf-8")

VERDE = "\033[32m"
ROJO = "\033[31m"
GRIS = "\033[90m"
NEGRITA = "\033[1m"
FIN = "\033[0m"


def paso(numero, titulo, comando, tolerar_fallo=False):
    print(f"\n{NEGRITA}[{numero}] {titulo}{FIN}")
    print(f"{GRIS}    $ {' '.join(comando[1:])}{FIN}\n")

    r = subprocess.run(comando, cwd=BASE_DIR, env=ENTORNO)

    if r.returncode != 0 and not tolerar_fallo:
        print(f"\n{ROJO}  Fallo en el paso {numero}. Se detiene aqui.{FIN}\n")
        sys.exit(1)

    return r.returncode


def main():
    rapido = "--rapido" in sys.argv
    sin_evals = "--sin-evals" in sys.argv

    print(f"\n{NEGRITA}Actualizando el asistente{FIN}")
    print(f"{GRIS}  fuente: perfil/*.md{FIN}")

    paso(1, "Copiar del perfil al corpus publico",
         [PY, "sync_data.py"])

    paso(2, "Regenerar embeddings e indice",
         [PY, "indexer.py"])

    if not sin_evals:
        cmd = [PY, "-m", "evals.run"]
        if rapido:
            cmd.append("--sin-juez")

        codigo = paso(3, "Comprobar que sigue respondiendo bien",
                      cmd, tolerar_fallo=True)

        if codigo != 0:
            print(f"\n{ROJO}  Hay casos fallando.{FIN}")
            print("  Si el cambio en el perfil los deja obsoletos, actualiza")
            print("  evals/cases.py. Si no, revisa que se rompio antes de publicar.\n")
            respuesta = input("  Continuar de todas formas? [s/N] ").strip().lower()
            if respuesta != "s":
                print("\n  Detenido. El indice local ya esta actualizado;")
                print("  no se ha copiado nada al portafolio.\n")
                sys.exit(1)

    paso(4, "Copiar el motor al repositorio del portafolio",
         [PY, "sync_api.py"])

    # Este paso falla fuerte a proposito. La tentacion es tolerarlo para
    # que la cadena no se corte cuando faltan credenciales de AWS, y esa
    # tolerancia es exactamente el bug que este paso vino a cerrar.
    paso(5, "Publicar el indice en S3, que es de donde lee Lambda",
         [PY, "publicar_indice.py"])

    print(f"\n{VERDE}{NEGRITA}  Listo.{FIN}")
    print(f"""
  {NEGRITA}AWS ya quedo actualizado.{FIN} El indice vive en S3, fuera del
  despliegue, asi que no hay imagen que reconstruir ni funcion que
  redesplegar. Lambda lo toma en el proximo arranque en frio.

  Falta Vercel, que sirve el indice desde su propio repositorio. Son dos
  pushes:

    {GRIS}# el proyecto del RAG{FIN}
    cd {BASE_DIR}
    git add -A && git commit -m "Actualizar el perfil del asistente" && git push

    {GRIS}# el portafolio: aqui vive la API que sirve la web{FIN}
    cd C:\\proyectos_portafolio\\Porfolio
    git add -A && git commit -m "Sincronizar el indice del asistente" && git push

  Vercel redespliega solo al recibir el push. El pipeline de AWS NO se
  dispara con esto, y es correcto: solo reacciona a cambios bajo aws/, y
  aqui no cambio el codigo de la funcion.
""")


if __name__ == "__main__":
    main()
