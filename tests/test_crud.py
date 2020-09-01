import pytest
import sqlite3

from .. import crud

def test_create_table():
    crud.create_tables('crud_test.db')

    conn = sqlite3.connect('crud_test.db')
    c = conn.cursor()
    c.execute ('''
                SELECT COUNT(name) 
                FROM sqlite_master 
                WHERE type="table" AND name="tasks" 
                ''' )
    count = c.fetchone()[0]
    conn.close()
    assert count == 1


def test_add_task():

    conn = sqlite3.connect('crud_test.db')
    c = conn.cursor()

    c.execute ('''
                SELECT COUNT(id) 
                FROM tasks 
                WHERE id="task1"
                ''' )
    count = c.fetchone()[0]
    assert count == 0

    crud.add_task('crud_test.db', 'task1', 'task_type_regular')    

    c.execute ('''
                SELECT COUNT(id) 
                FROM tasks 
                WHERE id="task1"
                ''' )
    count = c.fetchone()[0]
    conn.close()
    assert count == 1



def test_del_task():
    conn = sqlite3.connect('crud_test.db')
    c = conn.cursor()

    c.execute ('''
                SELECT COUNT(id) 
                FROM tasks 
                WHERE id="task1"
                ''' )
    count = c.fetchone()[0]
    assert count == 1

    crud.del_task('crud_test.db', 'task1')    

    c.execute ('''
                SELECT COUNT(id) 
                FROM tasks 
                WHERE id="task1"
                ''' )
    count = c.fetchone()[0]
    conn.close()
    assert count == 0


def test_get_tasks():
    conn = sqlite3.connect('crud_test.db')
    c = conn.cursor()

    c.execute ('''
                DELETE 
                FROM tasks 
                ''' )
    c.execute ('''
                SELECT COUNT(id) 
                FROM tasks
                ''' )
    count = c.fetchone()[0]
    assert count == 0

    c.execute( '''INSERT INTO tasks (id, type)
                    VALUES (?, ?)''',  ('task1', 'routine_task') )

    c.execute( '''INSERT INTO tasks (id, type)
                    VALUES (?, ?)''',  ('task2', 'cps_task') )

    c.execute( '''INSERT INTO tasks (id, type)
                    VALUES (?, ?)''',  ('task3', 'bw_task') )

    conn.commit()

    assert len(crud.get_tasks ('crud_test.db')) == 3