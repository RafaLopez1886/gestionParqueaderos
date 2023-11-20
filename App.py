from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_mysqldb import MySQL
from datetime import datetime
from flask import jsonify

app = Flask(__name__)
app.config["MYSQL_HOST"] = "127.0.0.1"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "parqueaderos"
mysql = MySQL(app)

app.secret_key = "mysecretkey"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/operaciones")
def operaciones():
    usuario_existe = False  # Inicializa como False
    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT usuarios.pk_usuarios AS Id, usuarios.usuarios_nombre AS Nombre, usuarios.usuarios_cedula AS Documento, gestion_vehiculos.vehiculos_marca AS Marca, vehiculos.nombre_tipoVehiculo AS Tipo, gestion_vehiculos.vehiculos_color AS Color, gestion_vehiculos.vehiculos_placa AS Placa, celdas.celdas_codigo AS Celda, gestion_vehiculos.vehiculos_ingreso AS Ingreso, gestion_vehiculos.vehiculos_salida AS Salida, gestion_vehiculos.vehiculos_observaciones AS Observaciones FROM gestion_vehiculos JOIN usuarios ON usuarios.usuarios_cedula = gestion_vehiculos.fk_usuarios JOIN vehiculos ON vehiculos.pk_tipoVehiculo = gestion_vehiculos.fk_tipoVehiculo JOIN celdas ON celdas.pk_celdas = gestion_vehiculos.fk_celda"
    )
    data = cur.fetchall()
    print(data)
    return render_template(
        "operaciones.html", usuario_existe=usuario_existe, usuarios=data
    )


@app.route("/usuarios")
def usuarios():
    usuario_existe = False  # Inicializa como False
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios")
    data = cur.fetchall()
    return render_template(
        "usuarios.html", usuario_existe=usuario_existe, usuarios=data
    )


@app.route("/celdas")
def celdas():
    usuario_existe = False  # Inicializa como False
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios")
    data = cur.fetchall()
    return render_template("celdas.html")

@app.route("/obtener_estado_celda/<string:celda>")
def obtener_estado_celda(celda):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT celdas_dispo FROM celdas WHERE celdas_codigo = %s", (celda,))
        estado_celda = cur.fetchone()[0]
        return jsonify({"dispo": estado_celda})
    except Exception as e:
        print("Error al obtener el estado de la celda:", str(e))
        return jsonify({"dispo": 0})  # En caso de error, considera la celda como no disponible

@app.route("/obtener_informacion_celda/<string:celda>")
def obtener_informacion_celda(celda):
    try:
        cur = mysql.connection.cursor()

        # Consulta para obtener información de la celda
        cur.execute("""
            SELECT 
                celdas.celdas_dispo AS disponibilidad,
                usuarios.usuarios_nombre AS usuario,
                usuarios.usuarios_telefono AS telefono
            FROM gestion_vehiculos
            JOIN usuarios ON usuarios.usuarios_cedula = gestion_vehiculos.fk_usuarios
            JOIN celdas ON gestion_vehiculos.fk_celda = celdas.pk_celdas
            WHERE celdas.celdas_codigo = %s
        """, (celda,))

        result = cur.fetchone()
        print(result)

        if result:
            # Si se encuentra la celda, devuelve la información
            return jsonify({
                "disponibilidad": 'Ocupada',
                "usuarioAsignado": result[1] or None,
                "telefonoAsignado": result[2] or None
            })
        else:
            # Si la celda no se encuentra, devuelve información por defecto
            return jsonify({
                "disponibilidad": 'Disponible',
                "usuarioAsignado": None,
                "telefonoAsignado": None
            })

    except Exception as e:
        print("Error al obtener información de la celda:", str(e))
        return jsonify({
            "disponibilidad": 0,
            "usuarioAsignado": None,
            "telefonoAsignado": None
        })



@app.route("/consultar_usuario", methods=["GET"])
def consultaUsuario():
    if request.method == "GET":
        documento = request.args.get("cedulaConsulta")
        cur = mysql.connection.cursor()
        numDocumento = cur.execute(
            "SELECT * FROM usuarios WHERE usuarios_cedula = %s", (documento,)
        )
        mysql.connection.commit()

        usuario_existe = numDocumento > 0

        if usuario_existe:
            usuario = cur.fetchone()
            session["usuario"] = usuario
        else:
            session["consulta_realizada"] = True

    return redirect(url_for("operaciones"))

@app.route("/consultar_usuario_usuarios", methods=["GET"])
def consultaUsuarioUsuarios():
    if request.method == "GET":
        documento = request.args.get("cedulaConsulta")
        cur = mysql.connection.cursor()
        numDocumento = cur.execute(
            "SELECT * FROM usuarios WHERE usuarios_cedula = %s", (documento,)
        )
        mysql.connection.commit()

        usuario_existe = numDocumento > 0

        if usuario_existe:
            usuario = cur.fetchone()
            session["usuario"] = usuario
        else:
            session["consulta_realizada"] = True

    return redirect(url_for("usuarios"))


@app.route('/eliminar_usuario/<string:id>', methods=['POST', 'GET'])
def eliminarUsuario(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM gestion_vehiculos WHERE fk_usuarios = {0}'.format(id))
    mysql.connection.commit()
    cur.execute('DELETE FROM usuarios WHERE pk_usuarios = {0}'.format(id))
    mysql.connection.commit()
    flash('Contact Removed Successfully')
    return redirect(url_for('usuarios'))


@app.route("/limpiar_resultado", methods=["GET"])
def limpiar_resultado():
    if "usuario" in session:
        del session["usuario"]
    return redirect(url_for("operaciones"))


@app.route("/limpiar_resultado_usuarios", methods=["GET"])
def limpiar_resultado_usuarios():
    if "usuario" in session:
        del session["usuario"]
    return redirect(url_for("usuarios"))

@app.route("/add_usuario", methods=["POST"])
def crearUsuario():
    if request.method == "POST":
        nombre = request.form["nombre"]
        cedula = request.form["cedula"]
        telefono = request.form["telefono"]
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO usuarios (usuarios_nombre, usuarios_cedula, usuarios_telefono) VALUES (%s, %s, %s)",
            (nombre, cedula, telefono),
        )
        mysql.connection.commit()
        flash("Usuario creado")
        return redirect(url_for("operaciones"))

@app.route("/add_operacion", methods=["POST"])
def crearOperacion():
    if request.method == "POST":
        cedula = request.form["cedulaParq"]
        tipo = request.form["tipoVehiculoParq"]
        marca = request.form["marcaParq"]
        color = request.form["colorParq"]
        placa = request.form["placaParq"]
        celda = request.form["celdaParq"]
        ingreso = request.form["ingresoParq"]
        observaciones = request.form["observacionesParq"]

        # Realiza la validación del usuario
        cur = mysql.connection.cursor()
        numDocumento = cur.execute(
            "SELECT * FROM usuarios WHERE usuarios_cedula = %s", (cedula,)
        )
        mysql.connection.commit()

        if numDocumento > 0:
            # El usuario existe, registra la operación
            try:
                # Busca la celda seleccionada y obtén su PK
                cur.execute("SELECT pk_celdas FROM celdas WHERE celdas_codigo = %s", (celda,))
                celda_pk = cur.fetchone()[0]

                # Busca la celda seleccionada y obtén su PK
                cur.execute("SELECT pk_tipoVehiculo FROM vehiculos WHERE nombre_tipoVehiculo = %s", (tipo,))
                tipo_pk = cur.fetchone()[0]

                # Busca la celda seleccionada y actualiza su disponibilidad a 0
                cur.execute("UPDATE celdas SET celdas_dispo = 0 WHERE celdas_codigo = %s", (celda,))
                mysql.connection.commit()

                # Registra la operación
                cur.execute(
                    "INSERT INTO gestion_vehiculos (fk_usuarios, fk_tipoVehiculo, vehiculos_marca, vehiculos_color, vehiculos_placa, "
                    "fk_celda, vehiculos_ingreso, vehiculos_observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (cedula, tipo_pk, marca, color, placa, celda_pk, ingreso, observaciones),
                )
                mysql.connection.commit()
                flash("Operación creada")
            except Exception as e:
                print("Error al crear la operación:", str(e))
                flash(
                    "Error al crear la operación: Ya existe un registro con la cédula proporcionada."
                    if "Duplicate entry" in str(e)
                    else "Error inesperado al crear la operación."
                )
        else:
            # El usuario no existe, muestra el modal para crear usuario
            flash("El usuario no existe. Por favor, crea un nuevo usuario.")
            return redirect(url_for("operaciones"))

        return redirect(url_for("operaciones")) 


@app.route("/crearOperacion")
def editarOperacion():
    return render_template("crearOperacion.html")


@app.route("/registrar_salida/<string:id>")
def registrarSalida(id):
    try:
        # Verifica si la función se está llamando correctamente
        print("Llamada a registrarSalida con id:", id)

        # Convierte id a cadena
        id = str(id)

        cur = mysql.connection.cursor()

        select_query = """
            SELECT gestion_vehiculos.pk_vehiculos
            FROM gestion_vehiculos
            JOIN usuarios ON usuarios.usuarios_cedula = gestion_vehiculos.fk_usuarios
            WHERE usuarios.pk_usuarios = %s
            AND gestion_vehiculos.vehiculos_salida IS NULL
        """

        # Ejecuta la consulta de selección
        cur.execute(select_query, (id,))
        result = cur.fetchone()

        if result:
            # Si se encuentra un registro válido, actualiza la salida
            pk_vehiculo = result[0]

            now = datetime.now()
            salida = now.strftime("%Y-%m-%d %H:%M:%S")

            # Consulta para actualizar la salida
            update_query = """
                UPDATE gestion_vehiculos
                SET vehiculos_salida = %s
                WHERE pk_vehiculos = %s
            """

            # Ejecuta la consulta de actualización
            cur.execute(update_query, (salida, pk_vehiculo))
            mysql.connection.commit()
            flash("Salida registrada exitosamente")
        else:
            flash(
                "El usuario con el id proporcionado no existe o la salida ya ha sido registrada"
            )

    except Exception as e:
        print("Error al registrar la salida:", str(e))
        flash("Error al registrar la salida")

    return redirect(url_for("operaciones"))


if __name__ == "__main__":
    app.run(port=3003, debug=True)
