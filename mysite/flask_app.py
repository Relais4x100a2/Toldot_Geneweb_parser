from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory, send_file, \
    jsonify, after_this_request
import os
from mysite import parser
from io import IOBase

app = Flask(__name__)
app.config.from_object('config.Config')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def processus_parser():
    export_parser = parser.parse()
    if export_parser == "Error_1":
        flash("Erreur, aucun fichier n'a été sélectionné pour être traité !", "danger")
        return render_template('index.html')
    elif export_parser == "Error_2":
        flash("Mauvais format de fichier, assurez-vous que le fichier soit bien au format Geneweb (.gw). Aucun "
              "fichier n'a été sauvegardé sur le serveur.", "danger")
        return render_template('index.html')
    else:
        return send_file(export_parser), os.remove(export_parser)

@app.errorhandler(413)
def too_large(e):
    flash("Le fichier est trop lourd, ne nous pouvons pas le traiter ! Réessayez avec un fichier plus léger. Aucun "
          "fichier n'a été sauvegardé sur le serveur.", "danger")
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True, port=5001)
