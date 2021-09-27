from flask import Flask, render_template, request, g, session, url_for, redirect
import sqlite3
import hashlib
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)

def connect_db():
    sql = sqlite3.connect('hello.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def hashpass(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    email = session['email']
    admin = session['admin']
    conn = get_db()
    sql = 'select id, username, email, admin from users order by id asc'
    cur = conn.execute(sql)
    data = cur.fetchall()
    return render_template('home.html', userlist=data, admin=admin)

@app.route('/test', methods=['GET','POST'])
def showtest():
    if request.method == 'POST':
        item = request.form['mytext']
    else:
        item = None
        
    return render_template('test.html', item=item)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        chkpass = hashpass(request.form['password'])
        conn = get_db()
        sql = 'select id, username, admin from users where email = ? and password = ?'
        results = conn.execute(sql, [email, chkpass])
        data = results.fetchone()
        if data is None:
            userdata = 'Username or password is incorrect'
        else:
            session['user'] = data['username']
            session['email'] = email
            session['admin'] = data['admin']
            userdata = 'user: {} logged in successfully'.format(data['username'])
            return redirect(url_for('home'))
    else:
        userdata = None
        
    return render_template('login.html', userdata=userdata)

@app.route('/edit/<uname>', methods=['GET', 'POST'])
def edit(uname):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        email = request.form['email']
        chkpass = request.form['chkpass']
        admin = request.form['admin']

        if pwd != chkpass:
            user = {'id': uname, 'username': user, 'email': email, 'admin': admin}
            return render_template('edit.html', user=user, msg='Passwords do not match')

        sql = 'update users set '
        paramcount = 0
        param = []
        joincond = ''
        if user.strip() != '':
            paramcount += 1
            param.append(user.strip())
            sql += joincond+'username = ?'
            joincond = ', '
        if email.strip() != '':
            paramcount += 1
            param.append(email.strip())
            sql += joincond+'email = ?'
            joincond = ', '
        if pwd.strip() != '':
            paramcount += 1
            param.append(hashpass(pwd.strip()))
            sql += joincond+'password = ?'
        if paramcount == 0:
            user = {'id': uname, 'username': user, 'email': email, 'admin': admin}
            return render_template('edit.html', user=user, msg='No Changes in Data')
        else:
            sql += ' where id = ?'
            param.append(uname)
            conn = get_db()
            cur = conn.execute(sql,param)
            conn.commit()
            return redirect(url_for('home'))

    conn = get_db()
    sql = 'select id, username, email, admin from users where id = ?'
    cur = conn.execute(sql, [uname])
    user = cur.fetchone()
    return render_template('edit.html', user=user, msg=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' not in session:
        return redirect(url_for('login'))

    admin = session['admin']

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        chkpass = request.form['chkpass']

        results = ""
        if chkpass != password:
            results = "Passwords don't match"
        else:
            conn = get_db()
            sql = 'insert into users (username, email, password) values (?, ?, ?)'
            try:
                conn.execute(sql, [username, email, hashpass(password)])
                conn.commit()
                return redirect(url_for('home'))
            except:
                results = 'Unable to register user - user exists'
            
        
    else:
        results = None

    return render_template('register.html', userdata=results, admin=admin)

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')
    if 'email' in session:
        session.pop('email')
    if 'admin' in session:
        session.pop('admin')

    return redirect(url_for('home'))

@app.route('/delete/<uid>')
def delete(uid):
    sql = 'delete from users where id = ?'
    conn = get_db()
    cur = conn.execute(sql, [uid])
    conn.commit()
    return redirect(url_for('home'))

@app.route('/promote/<uid>/<uadmin>')
def promote(uid,uadmin):
    if int(uadmin) == 0:
        sql = 'update users set admin = 1 where id = ?'
    else:
        sql = 'update users set admin = 0 where id = ?'
    conn = get_db()
    cur = conn.execute(sql, [uid])
    conn.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
    
