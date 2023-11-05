from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'parqueaderos'
mysql = MySQL(app)

app.secret_key = 'mysecretkey'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/operaciones')
def operaciones():
    usuario_existe = False  # Inicializa como False
    cur = mysql.connection.cursor()

    cur.execute('SELECT usuarios.pk_usuarios AS Id, usuarios.usuarios_nombre AS Nombre, usuarios.usuarios_cedula AS Documento, '
                'gestion_vehiculos.vehiculos_marca AS Marca, gestion_vehiculos.vehiculos_color AS Color, '
                'gestion_vehiculos.vehiculos_placa AS Placa, gestion_vehiculos.vehiculos_celda AS Celda, '
                'gestion_vehiculos.vehiculos_ingreso AS Ingreso, gestion_vehiculos.vehiculos_salida AS Salida, '
                'gestion_vehiculos.vehiculos_observaciones AS Observaciones FROM gestion_vehiculos JOIN usuarios ON '
                'usuarios.usuarios_cedula = gestion_vehiculos.fk_usuarios')
    data = cur.fetchall()
    return render_template('operaciones.html', usuario_existe=usuario_existe, usuarios=data)


@app.route('/consultar_usuario', methods=['GET'])
def consultaUsuario():
    if request.method == 'GET':
        documento = request.args.get('cedulaConsulta')
        cur = mysql.connection.cursor()
        numDocumento = cur.execute('SELECT * FROM usuarios WHERE usuarios_cedula = %s', (documento,))
        mysql.connection.commit()

        usuario_existe = numDocumento > 0

        if usuario_existe:
            usuario = cur.fetchone()
            session['usuario'] = usuario
        else:
            session['consulta_realizada'] = True

    return redirect(url_for('operaciones'))



@app.route('/limpiar_resultado', methods=['GET'])
def limpiar_resultado():
    if 'usuario' in session:
        del session['usuario']
    return redirect(url_for('operaciones'))
    

@app.route('/add_usuario', methods=['POST'])
def crearUsuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        cedula = request.form['cedula']
        telefono = request.form['telefono']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO usuarios (usuarios_nombre, usuarios_cedula, usuarios_telefono) VALUES (%s, %s, %s)', (nombre, cedula, telefono))
        mysql.connection.commit()
        flash('Usuario creado')
        return redirect(url_for('operaciones'))


@app.route('/add_operacion', methods=['POST'])
def crearOperacion():
    if request.method == 'POST':
        cedula = request.form['cedulaParq']
        marca = request.form['marcaParq']
        color = request.form['colorParq']
        placa = request.form['placaParq']
        celda = request.form['celdaParq']
        ingreso = request.form['ingresoParq']
        observaciones = request.form['observacionesParq']

        # Realiza la validación del usuario
        cur = mysql.connection.cursor()
        numDocumento = cur.execute('SELECT * FROM usuarios WHERE usuarios_cedula = %s', (cedula,))
        mysql.connection.commit()

        if numDocumento > 0:
            # El usuario existe, registra la operación
            try:
                cur.execute('INSERT INTO gestion_vehiculos (fk_usuarios, vehiculos_marca, vehiculos_color, vehiculos_placa, '
                            'vehiculos_celda, vehiculos_ingreso, vehiculos_observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s)', (cedula,
                                                                                                                 marca,
                                                                                                                 color,
                                                                                                                 placa,
                                                                                                                 celda, ingreso,
                                                                                                                 observaciones))
                mysql.connection.commit()
                flash('Operación creada')
            except Exception as e:
                flash(
                    'Error al crear la operación: Ya existe un registro con la cédula proporcionada.'
                    if 'Duplicate entry' in str(e)
                    else 'Error inesperado al crear la operación.')
        else:
            # El usuario no existe, muestra el modal para crear usuario
            flash('El usuario no existe. Por favor, crea un nuevo usuario.')
            return redirect(url_for('operaciones'))

        return redirect(url_for('operaciones'))
    

@app.route('/crearOperacion')
def editarOperacion():
    return render_template('crearOperacion.html')


@app.route('/registrar_salida/<string:id>')
def registrarSalida(id):
    try:
        # Verifica si la función se está llamando correctamente
        print("Llamada a registrarSalida con id:", id)

        # Convierte id a cadena
        id = str(id)

        cur = mysql.connection.cursor()

        select_query = '''
            SELECT gestion_vehiculos.pk_vehiculos
            FROM gestion_vehiculos
            JOIN usuarios ON usuarios.usuarios_cedula = gestion_vehiculos.fk_usuarios
            WHERE usuarios.pk_usuarios = %s
            AND gestion_vehiculos.vehiculos_salida IS NULL
        '''

        # Ejecuta la consulta de selección
        cur.execute(select_query, (id,))
        result = cur.fetchone()

        if result:
            # Si se encuentra un registro válido, actualiza la salida
            pk_vehiculo = result[0]

            now = datetime.now()
            salida = now.strftime("%Y-%m-%d %H:%M:%S")

            # Consulta para actualizar la salida
            update_query = '''
                UPDATE gestion_vehiculos
                SET vehiculos_salida = %s
                WHERE pk_vehiculos = %s
            '''

            # Ejecuta la consulta de actualización
            cur.execute(update_query, (salida, pk_vehiculo))
            mysql.connection.commit()
            flash('Salida registrada exitosamente')
        else:
            flash('El usuario con el id proporcionado no existe o la salida ya ha sido registrada')

    except Exception as e:
        print("Error al registrar la salida:", str(e))
        flash('Error al registrar la salida')

    return redirect(url_for('operaciones'))


if __name__ == '__main__':
    app.run(port=3003, debug=True)
