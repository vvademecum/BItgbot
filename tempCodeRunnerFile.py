r_id = message.from_user.id
    # username = message.from_user.username
    # firstName = message.from_user.first_name
    # lastName = message.from_user.last_name

    # cursor.execute('''INSERT INTO users (id, username, firstName, lastName, status) VALUES (%s, %s, %s, %s, '{RESIDENT}') 
    #                         On CONFLICT(id) DO UPDATE
    #                         SET (username, firstName, lastName, status) = (EXCLUDED.username, EXCLUDED.firstName, EXCLUDED.lastName, EXCLUDED.status);''', 
    #                         (user_id, username, firstName, lastName))

    # connection.commit()