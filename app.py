"""Punto de entrada compatible con la ejecución actual del proyecto."""
import webbrowser
from threading import Timer

from application import create_app

app = create_app()


if __name__ == "__main__":
    Timer(
        1,
        lambda: webbrowser.open("http://127.0.0.1:5000/"),
    ).start()

    app.run(debug=True, use_reloader=False)
