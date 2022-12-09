# Imports #
import sys
import socket
import chatlib


# Our server will run on same computer as client #
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5678


# HELPER SOCKET METHODS #
def build_and_send_message(socket_connection, cmd, data=""):
    """
    Explanations: Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.

    Parameters: socket_connection (socket object), cmd (str), data (str).

    Returns: Nothing.
    """
    full_msg = chatlib.build_message(cmd, data)
    print("[CLIENT] Client Send : " + full_msg)
    socket_connection.send(full_msg.encode())


def build_send_recv_parse(socket_connection, cmd, data=""):
    """
    Explanations: Builds a new message using chatlib, wanted code and message.
    Receives a new message from given socket, then parses the message using chatlib.

    Parameters: socket_connection (socket object), cmd (str), data (str).

    Returns: msg_code (str), return_data (str).
    """
    build_and_send_message(socket_connection, cmd, data)
    msg_code, return_data = recv_message_and_parse(socket_connection)
    return msg_code, return_data


def recv_message_and_parse(socket_connection):
    """
    Explanations: Receives a new message from given socket, then parses the message using chatlib.

    Parameters: socket_connection (socket object).

    Returns: msg_code (str) and data (str) of the received message.
    If error occurred, will return None, None.
    """
    full_msg = socket_connection.recv(1024).decode()
    msg_code, data = chatlib.parse_message(full_msg)
    return msg_code, data


def connect():
    """
    Explanations: Connect to socket.

    Returns: client_socket (socket object).
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    return client_socket


def error_and_exit(error_msg):
    """
    Explanations: Print error message and exit from the program.

    Parameters: error_msg (str).

    Returns: Nothing.
    """
    print(f'[CLIENT] Error Message : {error_msg} ...')
    sys.exit(1)


def login(socket_connection):
    """
    Explanations: Login to system.

    Parameters: socket_connection (socket object).

    Returns: Nothing.
    """
    while True:
        user_name = input("Please Enter Username : \n")
        password  = input("Please Enter Password : \n")
        build_and_send_message(socket_connection, chatlib.PROTOCOL_CLIENT["login_msg"], user_name + chatlib.DATA_DELIMITER + password)
        msg_code, login_data = recv_message_and_parse(socket_connection)

        if msg_code is not chatlib.ERROR_RETURN and msg_code == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
            print(f'[CLIENT] Logged In !')
            break
        else:
            print(f'[CLIENT] The Login Failed, Because : msg_code = {msg_code}  , login_data = {login_data} ...')


def logout(socket_connection):
    """
    Explanations: Logout from system.

    Parameters: socket_connection (socket object).

    Returns: Nothing.
    """
    build_and_send_message(socket_connection, chatlib.PROTOCOL_CLIENT["logout_msg"])
    print(f'[CLIENT] Logged Out !')


def get_score(socket_connection):
    """
    Explanations: Get score of user.

    Parameters: socket_connection (socket object).

    Returns: Nothing.
    """
    msg_code, my_score = build_send_recv_parse(socket_connection, cmd=chatlib.PROTOCOL_CLIENT["my_score_msg"])

    if msg_code is not chatlib.ERROR_RETURN and msg_code == chatlib.PROTOCOL_SERVER["your_score_msg"]:
        print(f'[CLIENT] Your Score is : {my_score}')
    else:
        error_and_exit(f'{chatlib.PROTOCOL_CLIENT["my_score_msg"]} Not Works, Because msg_code = {msg_code}')


def get_high_score(socket_connection):
    """
    Explanations: Get all the scores of users, and order them from the highest to lowest.

    Parameters: socket_connection (socket object).

    Returns: Nothing.
    """
    msg_code, high_score_table = build_send_recv_parse(socket_connection, cmd=chatlib.PROTOCOL_CLIENT["high_score_msg"])

    if msg_code is not chatlib.ERROR_RETURN and msg_code == chatlib.PROTOCOL_SERVER["all_score_msg"]:
        print("[CLIENT] High Score Table :" + "\n" + high_score_table)
    else:
        error_and_exit(f'{chatlib.PROTOCOL_CLIENT["high_score_msg"]} Not Works, Because msg_code = {msg_code}')


def play_question(socket_connection):
    """
    Explanations: Get question from the server, and get an answer also.

    Parameters: socket_connection (socket object).

    Returns: Nothing.
    """
    msg_code, question_data = build_send_recv_parse(socket_connection, cmd=chatlib.PROTOCOL_CLIENT["get_question_msg"])
    if msg_code is chatlib.ERROR_RETURN or msg_code == chatlib.PROTOCOL_SERVER["no_questions_msg"]:
        error_and_exit(f'{chatlib.PROTOCOL_CLIENT["get_question_msg"]} Game Over - Not Works, Because we don\'t have questions anymore in the stack ...')

    question_id, question_msg = question_data.split(chatlib.DATA_DELIMITER)
    print(f'[CLIENT] Question : {question_msg}' + '\n')

    user_answer = input("[CLIENT] Please Enter Your Answer : ")
    msg_code, server_answer = build_send_recv_parse(socket_connection, cmd=chatlib.PROTOCOL_CLIENT["send_answer_msg"], data=question_id + chatlib.DATA_DELIMITER + user_answer)

    if   msg_code == chatlib.PROTOCOL_SERVER["correct_answer_msg"]:
        print("[CLIENT] Great, The Answer is Correct !")

    elif msg_code == chatlib.PROTOCOL_SERVER["wrong_answer_msg"]:
        print(f'[CLIENT] Not Good, Your Answer is Not Correct. The Right Answer is Choice Number : {server_answer}')

    else:
        error_and_exit(f'{chatlib.PROTOCOL_CLIENT["send_answer_msg"]} Not Works, Because we didn\'t get answer from the Server ...')


def get_logged_users(socket_connection):
    """
    Explanations: Get all the logged users.

    Parameters: socket_connection (socket object).

    Returns: Nothing.
    """
    msg_code, logged_users = build_send_recv_parse(socket_connection, cmd=chatlib.PROTOCOL_CLIENT["logged_msg"])

    if msg_code is not chatlib.ERROR_RETURN and msg_code == chatlib.PROTOCOL_SERVER["logged_answer_msg"]:
        print("[CLIENT] Logged Users : " + "\n" + logged_users)
    else:
        error_and_exit(f'{chatlib.PROTOCOL_CLIENT["logged_msg"]} Not Works, Because msg_code = {msg_code}')


def main():
    client_socket = connect()
    print("[CLIENT] Server is Up and Running ...")

    login(client_socket)

    while True:
        print("==============================")
        print("P          | Play Question    ")
        print("S          | Get My Score     ")
        print("H          | Get High Score   ")
        print("L          | Get Logged Users ")
        print("Q          | Quit             ")
        print("==============================")

        user_choice = input("[CLIENT] Please Enter Your Choice : ")

        if   user_choice == "P":
            play_question(client_socket)

        elif user_choice == "S":
            get_score(client_socket)

        elif user_choice == "H":
            get_high_score(client_socket)

        elif user_choice == "L":
            get_logged_users(client_socket)

        elif user_choice == "Q":
            break

        else:
            print("[CLIENT] Wrong Input, Please try again ..." + "\n")

    logout(client_socket)
    client_socket.close()


if __name__ == '__main__':
    main()
