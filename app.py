"""
This program is meant to take debts and payments given a name. It should also store dates for this operations.

Aside from that, I want to build a Flask app to manage this, instead of using the console.
"""
import logging

from utils.database_managment import Database
from flask import Flask, redirect, render_template, url_for, session, request
from datetime import timedelta
from time import sleep


log = logging.getLogger('Fiados_logger.main_app')

WELCOME_STRING = """Bienvenido a la versión 2.0 del programa de deudas. Este le ayudará a llevar las deudas y pagos de
las distintas personas que interactúen con su negocio. Además, le permitirá ver el historial de
operaciones para algún cliente particular, así como revisar los saldos actuales."""

HOST = 'utils/database_file.db'

# Create the Database object for HOST
database = Database(HOST)
# Initialize and update the database.
database.initialize()
database.update()


### FLASK APP ###
log.debug('Initializing Flask app.')
app = Flask(__name__)
app.secret_key = "J@tAYGpzdCRL6C2jKBuW&8"
app.permanent_session_lifetime = timedelta(hours=8)
log.debug('Permanent session lifetime set')


@app.route('/')
def home():
    try:
        if session['user']:
            return render_template('index.html', WELCOME_STRING=WELCOME_STRING)
    except KeyError:
        return redirect(url_for('login'))
        

@app.route('/totals')
def display_totals():
    try:
        if session['user']:
            balances = database.show_balances()
            return render_template('saldos.html', balances=balances)
    except KeyError:
        return redirect(url_for('login'))


@app.route('/add', methods=['POST', 'GET'])
def add_operation():
    """
        Deals with adding an operation. 
        If the method is 'POST', then we check the form's info (if all neeeded fields are filled
        are they filled with correct values?, etc.)
        If the method is GET, it just renders the template.
    """
    try:
        log.debug("Checking for session")
        if session['user']:
            log.debug(f"Session for {session['user']} found.")
            try:
                if request.method == 'POST':
                    log.debug("POST request received. Getting the form's data")
                    old_name = '' if request.form['old_client'] == 'No está en la lista' else request.form['old_client']
                    new_name = request.form['new_client']
                    try:
                        amount = float(str(request.form['amount']).strip().strip('-'))
                    except ValueError:
                        return redirect(url_for('add_operation'))                    
                    operation = request.form['op_radio']                    
                    if (old_name or new_name) and amount:
                        log.debug('Conditions for adding operation matched. Checking the names')
                        if not old_name:
                            name = new_name
                        else:
                            name = old_name
                        database.add_operation(name, amount, operation)
                        log.debug(f"Added {name.title()}'s {operation} for $%.2f" % amount)
                        log.debug(f"Changing values in strings for showing them.")
                        operation = 'La deuda' if operation == 'debt' else 'El pago'
                        return render_template('successfull.html', name=name, amount=amount, operation=operation)
                    else:
                        log.error('Adding conditions unmatched. Refreshing the page.')
                        return redirect(url_for('add_operation'))
                else:
                    log.debug("GET request received. Getting the clients and rendering html.")
                    clients = database.get_clients()
                    return render_template('add_operation.html', clients=clients)
            except:
                raise
    except KeyError:
        log.error("No session found. Time to redirect to login.")
        return redirect(url_for('login'))


@app.route('/success')
def succesfully_added(name: str, amount: float, operation: str):
    """
        This route renders a 'successfully added' page. Waits a little and then renders back the 'add' one.
    """

    log.debug('Success page wanting to render. Checking if there is a session')
    try:
        if session['user']:
            if request.method == 'GET':
                log.debug('GET request received. Rendering the template.')
                return render_template('successfull.html', name=name.title(), amount=amount, operation=operation)
            elif request.method == 'POST':
                log.debug('POST request received. Checking the buttons.')
    except KeyError:
        return redirect(url_for('login'))


@app.route('/operations')
def operations():
    """
        This route deals with showhing operations for a specific person.
    """
    try:
        log.debug("Checking for session")
        if session['user']:
            if request.method == 'GET':
                return render_template('operations.html')
            elif request.method == 'POST':
                pass
    except KeyError:
        return redirect(url_for('login'))


# LOGIN AND LOGOUT
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
        Checks the login info.
    """
    if request.method == 'POST':
        session.permament = True
        user = request.form['user']
        password = request.form['pass']
        if database.check_login(user, password):
            session['user'] = user
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
        Pops off the 'user' value in the session variable. Logs out, that's what happens if you do that.
    """
    session.pop('user', None)
    return redirect(url_for('home'))

### FLASK RUN ONLY IF THIS IS THE MAIN SCRIPT ###
if __name__ == '__main__':
    app.run(debug=True)
    

