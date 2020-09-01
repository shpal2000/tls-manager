import sqlite3

def create_tables(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    c.execute (''' DROP TABLE IF EXISTS tasks''')

    c.execute (''' CREATE TABLE tasks
                        (id text PRIMARY KEY, type text NOT NULL)''')
                        
    conn.commit()
    conn.close()

def add_task(db_file, task_id, task_type):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    c.execute( '''INSERT INTO tasks (id, type)
                    VALUES (?, ?)''',  (task_id, task_type) )
                        
    conn.commit()
    conn.close()

def del_task(db_file, task_id):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    c.execute( '''DELETE FROM tasks
                    WHERE id = ?''',  (task_id,) )
                        
    conn.commit()
    conn.close()

def get_tasks(db_file):
    tasks = []
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    for row in c.execute ('''SELECT id FROM tasks'''):
        tasks.append ({"id" : row[0]})
                       
    conn.commit()
    conn.close()
    return tasks