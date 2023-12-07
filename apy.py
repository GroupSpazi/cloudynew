from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
from datetime import datetime
import pymysql
from flask_mysqldb import MySQL
import MySQLdb



app = Flask(__name__)

# Configura la conexión a la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'cloudy1'

mysql = MySQL(app)

# Configura una clave secreta para la sesión de Flask
app.secret_key = 'tu_clave_secreta'

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('admin/login_admin.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM login_admin WHERE usuario = %s AND contrasena = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('admin/login_admin.html', error='Credenciales incorrectas')


@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT p.nombre, p.apellido_paterno FROM perfil_empleado p JOIN login_admin l ON p.usuario = l.usuario WHERE l.usuario = %s", [session['username']])
        user_data = cursor.fetchone()
        if user_data:
            nombre = user_data[0]
            apellido_paterno = user_data[1]
        else:
            nombre = ""
            apellido_paterno = ""

        # Obtener la hora actual
        current_hour = datetime.now().hour

        # Determinar el saludo
        if 6 <= current_hour < 12:
            greeting = "BUENOS DÍAS"
        elif 12 <= current_hour < 18:
            greeting = "BUENAS TARDES"
        else:
            greeting = "BUENAS NOCHES"

        return render_template('admin/dashboard_admin.html', username=session['username'], nombre=nombre, apellido_paterno=apellido_paterno, greeting=greeting)
    return redirect(url_for('index'))




@app.context_processor
def inject_greeting_and_user_data():
    # Obtener la hora actual
    current_hour = datetime.now().hour

    # Determinar el saludo
    if 6 <= current_hour < 12:
        greeting = "BUENOS DÍAS"
    elif 12 <= current_hour < 18:
        greeting = "BUENAS TARDES"
    else:
        greeting = "BUENAS NOCHES"

    if 'username' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT p.nombre, p.apellido_paterno FROM perfil_empleado p JOIN login_admin l ON p.usuario = l.usuario WHERE l.usuario = %s", [session['username']])
        user_data = cursor.fetchone()
        if user_data:
            nombre = user_data[0]
            apellido_paterno = user_data[1]
        else:
            nombre = ""
            apellido_paterno = ""
    else:
        nombre = ""
        apellido_paterno = ""

    return {'greeting': greeting, 'nombre': nombre, 'apellido_paterno': apellido_paterno}







def get_all_users():
    cursor = mysql.connection.cursor()
    # Solo seleccionamos 'usuario' y 'role' de la consulta
    cursor.execute("SELECT usuario, role FROM login_admin")
    users = cursor.fetchall()
    return users

def get_roles():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT DISTINCT role FROM login_admin")
    roles = [item[0] for item in cursor.fetchall()]
    return roles

@app.route('/roles')
def roles():
    if 'username' in session:
        users = get_all_users()
        roles = get_roles()
        return render_template('admin/roles.html', username=session['username'], users=users, roles=roles)
    return redirect(url_for('index'))


@app.route('/update_roles', methods=['POST'])
def update_roles():
    if 'username' in session:
        cursor = mysql.connection.cursor()
        for user in request.form:
            if user.startswith("role_"):
                username = user.split("_")[1]
                new_role = request.form[user]
                cursor.execute("UPDATE login_admin SET role = %s WHERE usuario = %s", (new_role, username))
        mysql.connection.commit()
        flash('Roles actualizados con éxito', 'success')
        return redirect(url_for('roles'))
    else:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/perfil_trabajador', methods=['GET', 'POST'])
def perfil_trabajador():
    if 'username' in session:
        cursor = mysql.connection.cursor()
        
        if request.method == 'POST':
            # Datos de login_admin
            usuario = request.form['usuario']
            contrasena = request.form['contrasena']
            rol_erp = request.form['rol_erp']

            # Datos de perfil_empleado
            nombre = request.form['nombre']
            apellido_paterno = request.form['apellido_paterno']
            apellido_materno = request.form['apellido_materno']
            telefono = request.form['telefono']
            correo = request.form['correo']

            # Actualizar datos en login_admin
            cursor.execute("UPDATE login_admin SET usuario=%s, contrasena=%s, role=%s WHERE usuario=%s", 
                           (usuario, contrasena, rol_erp, session['username']))
            
            # Verificar si el usuario ya tiene un perfil en perfil_empleado
            cursor.execute("SELECT * FROM perfil_empleado WHERE usuario = %s", [usuario])
            if cursor.fetchone():
                # Si ya tiene perfil, actualizar
                cursor.execute("UPDATE perfil_empleado SET nombre=%s, apellido_paterno=%s, apellido_materno=%s, telefono=%s, correo=%s WHERE usuario=%s", 
                               (nombre, apellido_paterno, apellido_materno, telefono, correo, usuario))
            else:
                # Si no tiene perfil, insertar nuevo
                cursor.execute("INSERT INTO perfil_empleado (usuario, nombre, apellido_paterno, apellido_materno, telefono, correo) VALUES (%s, %s, %s, %s, %s, %s)", 
                               (usuario, nombre, apellido_paterno, apellido_materno, telefono, correo))
            
            mysql.connection.commit()
            flash('Perfil actualizado con éxito', 'success')
        
        # Obtener los datos del usuario logueado
        cursor.execute("SELECT l.usuario, l.role, l.contrasena, p.nombre, p.apellido_paterno, p.apellido_materno, p.telefono, p.correo FROM login_admin l LEFT JOIN perfil_empleado p ON l.usuario = p.usuario WHERE l.usuario = %s", [session['username']])
        user_data = cursor.fetchone()
        
        return render_template('admin/perfil_trabajador.html', username=session['username'], user_data=user_data)
    return redirect(url_for('index'))



@app.route('/ventas/nuevocf', methods=['GET', 'POST'])
def nuevocf():
    if request.method == 'POST':
        # Recopila todos los datos del formulario
        identificador = request.form['identificador']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        fecha_nacimiento = request.form['fecha_nacimiento']
        sexo = request.form['sexo']
        curp = request.form['curp']
        assigned_to = request.form['assigned_to']
        telefono_principal = request.form['telefono_principal']
        codigo_postal = request.form['codigo_postal']
        estado = request.form['estado']
        municipio = request.form['municipio']
        colonia = request.form['colonia']
        calle = request.form['calle']
        num_exterior = request.form['num_exterior']
        num_interior = request.form['num_interior']
        google_maps_url = request.form['google_maps_url']

        # Inserta los datos en la tabla clients_cf
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO clients_cf (identificador, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, curp, assigned_to, telefono_principal, codigo_postal, estado, municipio, colonia, calle, num_exterior, num_interior, google_maps_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (identificador, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, curp, assigned_to, telefono_principal, codigo_postal, estado, municipio, colonia, calle, num_exterior, num_interior, google_maps_url))
        mysql.connection.commit()

        # Muestra un mensaje de éxito
        flash('Cliente guardado exitosamente', 'success')
        return redirect(url_for('nuevocf'))

    user = obtener_usuario_actual()
    vendedores = obtener_vendedores()
    return render_template('admin/nuevocf.html', current_user=user, vendedores=vendedores)





@app.route('/get_info_by_cp/<cp>', methods=['GET'])
def get_info_by_cp(cp):
    cur = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sepomex WHERE d_codigo = %s", [cp])
    results = cur.fetchall()
    cur.close()
    
    if results:
        data = {
            'estado': results[0]['d_estado'],
            'municipio': results[0]['d_mnpio'],
            'colonias': [row['d_asenta'] for row in results]
        }
        return jsonify(data)
    else:
        return jsonify({'error': 'No se encontró información para ese código postal'}), 404


# Logica Si el usuario logueado es un vendedor, se asignará automáticamente a él. Si el usuario es un administrador, podrá seleccionar a qué vendedor asignar.
def obtener_usuario_actual():
    if 'username' in session:
        cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM login_admin WHERE usuario = %s", [session['username']])
        user = cursor.fetchone()
        if user:
            user['role'] = user['role'].lower()
        return user
    return None



@app.route('/ruta_a_tu_vista')
def tu_vista():
    user = obtener_usuario_actual()
    if not user:
        return redirect(url_for('index'))

    if user['role'] == 'vendedor':  # Ajustado a minúsculas
        assigned_user = user['usuario']
    elif user['role'] == 'administrador':  # Ajustado a minúsculas
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT usuario FROM login_admin WHERE role = 'vendedor'")  # Ajustado a minúsculas
        vendedores = cursor.fetchall()
        return render_template('seleccionar_vendedor.html', vendedores=vendedores)
    else:
        return redirect(url_for('index'))

    return render_template('nombre_de_tu_plantilla.html', current_user=user, assigned_user=assigned_user)



def obtener_vendedores():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT usuario FROM login_admin WHERE role = 'vendedor'")
    vendedores = cursor.fetchall()
    return vendedores

# Aqui termina lo de formulario CF 


# Aqui inicia lo de formulario CI 

@app.route('/ventas/nuevoci', methods=['GET', 'POST'])
def nuevoci():
    if request.method == 'POST':
        # Recopila todos los datos del formulario
        identificador = request.form['identificador']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        fecha_nacimiento = request.form['fecha_nacimiento']
        sexo = request.form['sexo']
        curp = request.form['curp']
        assigned_to = request.form['assigned_to']
        telefono_principal = request.form['telefono_principal']
        codigo_postal = request.form['codigo_postal']
        estado = request.form['estado']
        municipio = request.form['municipio']
        colonia = request.form['colonia']
        calle = request.form['calle']
        num_exterior = request.form['num_exterior']
        num_interior = request.form['num_interior']
        google_maps_url = request.form['google_maps_url']
        giro_instalador = request.form['giro_instalador']
        
        # Para checkboxes, obtendrás una lista de valores seleccionados
        marcas_compra = request.form.getlist('marcas_compra')
        marcas_compra_str = ",".join(marcas_compra)

        # Inserta los datos en la tabla clients_ci
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO clients_ci (identificador, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, curp, assigned_to, telefono_principal, codigo_postal, estado, municipio, colonia, calle, num_exterior, num_interior, google_maps_url, giro_instalador, marcas_compra) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (identificador, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, curp, assigned_to, telefono_principal, codigo_postal, estado, municipio, colonia, calle, num_exterior, num_interior, google_maps_url, giro_instalador, marcas_compra_str))
        mysql.connection.commit()

        # Muestra un mensaje de éxito
        flash('Cliente guardado exitosamente', 'success')
        return redirect(url_for('nuevoci'))






    user = obtener_usuario_actual()
    vendedores = obtener_vendedores()
    return render_template('admin/nuevoci.html', current_user=user, vendedores=vendedores)






@app.route('/ventas/general', methods=['GET', 'POST'])
def generalclients():
    search_term = request.form.get('search_term', '')
    assigned_to = request.form.get('assigned_to', '')
    identifier_type = request.form.get('identifier_type', 'Todos')

    cursor = mysql.connection.cursor()

    # Se añadió el campo "id" al inicio de la consulta
    base_query = "SELECT id, assigned_to, identificador, nombre, apellido_paterno, apellido_materno, telefono_principal, estado, municipio FROM {} WHERE 1=1"
    
    params = []
    search_clause = ""

    if search_term:
        search_clause = """ AND (identificador LIKE %s OR 
                                  nombre LIKE %s OR 
                                  apellido_paterno LIKE %s OR 
                                  apellido_materno LIKE %s OR 
                                  telefono_principal LIKE %s OR 
                                  estado LIKE %s OR 
                                  municipio LIKE %s OR 
                                  assigned_to LIKE %s)"""
        params.extend(['%' + search_term + '%'] * 8)

    if assigned_to:
        params.append(assigned_to)

    if identifier_type == "CF":
        query = base_query.format("clients_cf")
        if assigned_to:
            query += " AND assigned_to = %s"
        query += search_clause
    elif identifier_type == "CI":
        query = base_query.format("clients_ci")
        if assigned_to:
            query += " AND assigned_to = %s"
        query += search_clause
    else:
        query_cf = base_query + search_clause
        if assigned_to:
            query_cf += " AND assigned_to = %s"
        query_cf = query_cf.format("clients_cf")
        
        query_ci = base_query + search_clause
        if assigned_to:
            query_ci += " AND assigned_to = %s"
        query_ci = query_ci.format("clients_ci")
        
        query = query_cf + " UNION " + query_ci
        params = params * 2

    cursor.execute(query, params)
    clients = cursor.fetchall()

    cursor.execute("SELECT usuario FROM login_admin WHERE role = 'vendedor'")
    vendedores = cursor.fetchall()

    return render_template('admin/generalclients.html', clients=clients, vendedores=vendedores, search_term=search_term, assigned_to=assigned_to, identifier_type=identifier_type)



#Aqui inicia para poder ver los datos del cliente en el perfil

@app.route('/ver_cliente/<tipo>/<client_id>')
def ver_cliente(tipo, client_id):
    cursor = mysql.connection.cursor()

    # Agregando mensaje de depuración para ver el identificador que estamos buscando
    print(f"Buscando cliente del tipo: {tipo} con ID: {client_id}")

    if tipo == "CF":
        cursor.execute("SELECT * FROM clients_cf WHERE identificador = %s AND id = %s", [tipo, client_id])
        
        # Ahora extraemos las columnas después de haber ejecutado la consulta
        columns = [desc[0] for desc in cursor.description]
        
        row = cursor.fetchone()
        
        # Transforma el resultado en un diccionario
        cliente_data = dict(zip(columns, row))
         
        # Imprimir la información del cliente para depuración
        print(cliente_data)

        if cliente_data:
            return render_template('admin/cliente_cf.html', cliente=cliente_data)
        else:
            return "Cliente no encontrado", 404

    elif tipo == "CI":
        cursor.execute("SELECT * FROM clients_ci WHERE identificador = %s AND id = %s", [tipo, client_id])
        
        # Nuevamente, extraemos las columnas después de haber ejecutado la consulta
        columns = [desc[0] for desc in cursor.description]
        
        row = cursor.fetchone()
        
        # Transforma el resultado en un diccionario
        cliente_data = dict(zip(columns, row))
        
        # Imprimir la información del cliente para depuración
        print(cliente_data)

        if cliente_data:
            return render_template('admin/cliente_ci.html', cliente=cliente_data)
        else:
            return "Cliente no encontrado", 404

    else:
        return "Identificador no válido", 400




@app.route('/actualizar_cliente/<tipo>/<client_id>', methods=['POST'])
def actualizar_cliente(tipo, client_id):
    nombre = request.form.get('nombre')
    apellido_paterno = request.form.get('apellido_paterno')
    apellido_materno = request.form.get('apellido_materno')
    
    # Campos adicionales
    fecha_nacimiento = request.form.get('fecha_nacimiento')
    sexo = request.form.get('sexo')
    curp = request.form.get('curp')
    telefono_principal = request.form.get('telefono_principal')
    
    # Campos relacionados con la dirección
    codigo_postal = request.form.get('codigo_postal')
    estado = request.form.get('estado')
    municipio = request.form.get('municipio')
    colonia = request.form.get('colonia')
    calle = request.form.get('calle')
    num_exterior = request.form.get('num_exterior')
    num_interior = request.form.get('num_interior')
    google_maps_url = request.form.get('google_maps_url')  # Obtiene la URL de Google Maps desde el formulario

    cursor = mysql.connection.cursor()

    if tipo == "CF":
        cursor.execute("""
            UPDATE clients_cf SET 
            nombre=%s, apellido_paterno=%s, apellido_materno=%s,
            fecha_nacimiento=%s, sexo=%s, curp=%s, telefono_principal=%s, 
            codigo_postal=%s, estado=%s, municipio=%s, colonia=%s, 
            calle=%s, num_exterior=%s, num_interior=%s, google_maps_url=%s
            WHERE identificador=%s AND id=%s
        """, (nombre, apellido_paterno, apellido_materno, 
              fecha_nacimiento, sexo, curp, telefono_principal,
              codigo_postal, estado, municipio, colonia, calle, num_exterior, 
              num_interior, google_maps_url, tipo, client_id))
    elif tipo == "CI":
        cursor.execute("""
            UPDATE clients_ci SET 
            nombre=%s, apellido_paterno=%s, apellido_materno=%s,
            fecha_nacimiento=%s, sexo=%s, curp=%s, telefono_principal=%s, 
            codigo_postal=%s, estado=%s, municipio=%s, colonia=%s, 
            calle=%s, num_exterior=%s, num_interior=%s, google_maps_url=%s
            WHERE identificador=%s AND id=%s
        """, (nombre, apellido_paterno, apellido_materno, 
              fecha_nacimiento, sexo, curp, telefono_principal,
              codigo_postal, estado, municipio, colonia, calle, num_exterior, 
              num_interior, google_maps_url, tipo, client_id))
    else:
        return "Identificador no válido", 400
    
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('ver_cliente', tipo=tipo, client_id=client_id))












if __name__ == '__main__':
    app.run(debug=True)
