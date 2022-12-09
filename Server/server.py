import os
import copy
import base64
import select
import socket
import random
import chatlib
import requests


# Global Variables #
users        	     = {}
questions    	     = {}
logged_users 	     = {}
messages_to_send     = []
ERROR_MSG    	     = "Error !"
SERVER_PORT  	     = 5678
SERVER_IP    	     = "127.0.0.1"
CORRECT_ANSWER_POINT = 5


# HELPER SOCKET METHODS #
def build_and_send_message(socket_connection, cmd, data=""):
	"""
	Explanations: Builds a new message using chatlib, wanted cmd and message.
	Prints debug info, then sends it to the given socket.

	Parameters: socket_connection (socket object), cmd (str), data (str).

	Returns: Nothing.
	"""
	global messages_to_send

	full_msg = chatlib.build_message(cmd, data)
	print("[SERVER] ", full_msg)

	"""
	Explanations ===>
	For One Client       : socket_connection.send(full_msg.encode())
	For Multiple Clients : messages_to_send.append((socket_connection.getpeername(), data))
	"""
	messages_to_send.append((socket_connection, data))


def recv_message_and_parse(socket_connection):
	"""
	Explanations: Receives a new message from given socket, then parses the message using chatlib.

	Parameters: socket_connection (socket object).

	Returns: msg_code (str) and data (str) of the received message.
	If error occurred, will return None, None.
	"""
	full_msg = socket_connection.recv(1024).decode()
	print("[CLIENT] ", full_msg)
	msg_code, data = chatlib.parse_message(full_msg)
	return msg_code, data
	

# DATA LOADERS #
def load_questions():
	"""
	Explanations: Loads questions bank from file.

	Example :
	questions = {
					2313 : {"question": "How much is 2 + 2"              , "answers": ["3", "4", "2", "1"]                        , "correct": 2},
					4122 : {"question": "What is the capital of France ?", "answers": ["Lion", "Marseille", "Paris", "Montpelier"], "correct": 3}
				}

	Returns: questions dictionary.
	"""
	global questions

	with open(os.path.join(os.getcwd(), "questions.txt"), 'r') as content_to_read:
		for line_to_read in content_to_read:
			if line_to_read.count("|") == 5:
				question_fields = [question_field.strip() for question_field in line_to_read.split("|")[1:-1]]
				if "Question ID" == question_fields[0]: continue
				question_id, question, answers, correct_answer = question_fields
				answers = [int(answer.strip()) for answer in answers.split(",")]
				questions[question_id] = {"question": question, "answers": answers, "correct": correct_answer}

	return questions


def load_user_database():
	"""
	Explanations: Loads users list from file.

	Example :
	users = {
				"test"   :	{"password": "test"  , "score": 0  , "questions_asked":[]},
				"yossi"	 :	{"password": "123"   , "score": 50 , "questions_asked":[]},
				"master" :	{"password": "master", "score": 200, "questions_asked":[]}
			}

	Returns: user dictionary.
	"""
	global users

	with open(os.path.join(os.getcwd(), "users.txt"), 'r') as content_to_read:
		for line_to_read in content_to_read:
			if line_to_read.count("|") == 5:
				user_fields = [user_field.strip() for user_field in line_to_read.split("|")[1:-1]]
				if "User Name" == user_fields[0]: continue
				user_name, password, score, questions_asked = user_fields
				if questions_asked == "-": questions_asked = []
				else:                      questions_asked = questions_asked.split(",")
				users[user_name] = {"password": password, "score": int(score), "questions_asked": questions_asked}

	return users


def load_questions_from_web():
	"""
	Explanations: Get questions from Web Page.

	Example :
	questions = {
					2313 : {"question": "How much is 2 + 2"              , "answers": ["3", "4", "2", "1"]                        , "correct": 2},
					4122 : {"question": "What is the capital of France ?", "answers": ["Lion", "Marseille", "Paris", "Montpelier"], "correct": 3}
				}

	Returns: questions (dict).
	"""
	global questions

	web_response = requests.get("https://opentdb.com/api.php?amount=50&difficulty=easy&type=multiple&encode=base64")
	web_text     = web_response.json()
	for idx, web_question in enumerate(web_text['results'], start=1):
		question       = base64.b64decode(web_question["question"]).decode('utf-8')
		answers        = [base64.b64decode(web_question["correct_answer"]).decode('utf-8')] + [base64.b64decode(incorrect_answers).decode('utf-8') for incorrect_answers in web_question["incorrect_answers"]]
		correct_answer = base64.b64decode(web_question["correct_answer"]).decode('utf-8')
		questions[idx] = {"question": question, "answers": answers, "correct": correct_answer}

	return questions


# SOCKET CREATOR #
def setup_socket():
	"""
	Explanations: Creates new listening socket and returns it.

	Returns: The socket object.
	"""
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind((SERVER_IP, SERVER_PORT))
	server_socket.listen()
	print("[SERVER] Server is Up and Running ...")
	return server_socket
	

def send_error(socket_connection, error_msg):
	"""
	Explanations: Send error message with given message.

	Receives: socket_connection (socket object), message error string from called function.

	Returns: None.
	"""
	cmd        = chatlib.PROTOCOL_SERVER["login_failed_msg"] + (" " * (chatlib.CMD_FIELD_LENGTH - len(chatlib.PROTOCOL_SERVER["login_failed_msg"])))
	str_length = str(len(error_msg)).zfill(4)
	full_msg   = cmd + "|" + str_length + "|" + error_msg
	socket_connection.send(full_msg.encode())
	

# MESSAGE HANDLING #
def handle_get_score_message(socket_connection, user_name):
	"""
	Explanations: Handle with your score message.

	Receives: socket_connection (socket object), user_name (str).

	Returns: None.
	"""
	global users
	build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["YOUR_SCORE"], str(users[user_name]["score"]))


def handle_high_score_message(socket_connection):
	"""
	Explanations: Handle high score message.

	Receives: socket_connection (socket object).

	Returns: None.
	"""
	global users

	data = ""
	sortedDict = dict(sorted(users.items(), key=lambda item: item[1]["score"], reverse=True))
	for user, user_details in sortedDict.items():
		data += user + " : " + str(user_details["score"]) + "\n"

	build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["all_score_msg"], data)


def handle_logout_message(socket_connection):
	"""
	Explanations: Closes the given socket (in later chapters, also remove user from logged_users dictionary).

	Receives: socket_connection (socket object).

	Returns: None.
	"""
	global logged_users

	"""
	Explanations :
	user_port = socket_connection.getpeername()[0] 
	user_ip   = socket_connection.getpeername()[1]
	"""
	user_ip = socket_connection.getpeername()[1]
	del logged_users[user_ip]
	socket_connection.close()


def handle_login_message(socket_connection, data):
	"""
	Explanations: Gets socket and message data of login message. Checks  user and pass exists and match.
	If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users.

	Receives: socket_connection (socket object), data (str).

	Returns: None.
	"""
	global users         # This is needed to access the same users' dictionary from all functions
	global logged_users	 # To be used later

	user_name, password = chatlib.split_data(msg=data, expected_delimeters=1)

	if user_name in users:
		if users[user_name]["password"] == password:
			user_ip = socket_connection.getpeername()[1]
			logged_users[user_ip] = user_name
			build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["login_ok_msg"])
		else:
			data = "[SERVER] Password Incorrect ..."
			build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["login_failed_msg"], data)
	else:
		data = f'[SERVER] User {user_name} Not Exist in the DB of the Server ...'
		build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["login_failed_msg"], data)


def handle_logged_message(socket_connection):
	"""
	Explanations: Handle logged users.

	Receives: socket_connection (socket object).

	Returns: -
	"""
	global users

	data = ""
	for idx, user in enumerate(users.keys()):
		comma = "" if idx == len(users.keys()) - 1 else ", "
		data += user + comma

	build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["logged_answer_msg"], data)


def handle_client_message(socket_connection, cmd, data):
	"""
	Explanations: Gets message cmd and data and calls the right function to handle command.

	Receives: socket_connection (socket object), cmd (str) and data (str).

	Returns: None.
	"""
	global logged_users

	user_name = socket_connection.gethostname()
	if user_name not in logged_users.values():
		if  cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
			handle_login_message(socket_connection, data)
		else:
			data = f'[SERVER] The user not logged into the System, so the cmd : {cmd} - Not Recognized ...'
			build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["login_failed_msg"], data)
	else:
		if   cmd == chatlib.PROTOCOL_CLIENT["logged_msg"]:
			handle_logged_message(socket_connection)

		elif cmd == chatlib.PROTOCOL_CLIENT["my_score_msg"]:
			user_name = socket_connection.gethostname()
			handle_get_score_message(socket_connection, user_name)

		elif cmd == chatlib.PROTOCOL_CLIENT["high_score_msg"]:
			handle_high_score_message(socket_connection)

		elif cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
			handle_logout_message(socket_connection)

		elif cmd == chatlib.PROTOCOL_CLIENT["get_question_msg"]:
			handle_question_message(socket_connection)

		elif cmd == chatlib.PROTOCOL_CLIENT["send_answer_msg"]:
			handle_answer_message(socket_connection, user_name, data)

		else:
			data = f'[SERVER] The cmd : {cmd} - Not Recognized ...'
			build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["login_failed_msg"], data)


def create_random_question(user_name):
	"""
	Explanations: Get random question.

	Algorithm :
	1 - Get Random question (with all details of question).
	2 - If question not asked already by the client, we can send the question to the client.
	    Else, we need to remove this question from the temporary DB that we have.
	    Then, we need to check if the DB of questions is empty or not :
	    * if the DB is empty    ---> We return None.
	    * if the DB isn't empty ---> We try to random new question ID.

	Returns: data (str).
	"""
	global users
	global questions

	questionsCopy = copy.deepcopy(questions)

	while True:
		id_question, question_details = random.choice(list(questionsCopy.items()))
		if id_question not in users[user_name]["questions_asked"]:
			break
		else:
			del questionsCopy[int(id_question)]
			if len(questionsCopy) == 0:
				return None

	data = str(id_question) + chatlib.DATA_DELIMITER + question_details["question"] + chatlib.DATA_DELIMITER + chatlib.DATA_DELIMITER.join(question_details["answers"])
	return data


def handle_question_message(socket_connection):
	"""
	Explanations: Send question to Client.

	Receives: socket_connection (socket object).

	Returns: None.
	"""
	global logged_users

	socket_connection_ip = socket_connection.getpeername()[1]
	data = create_random_question(logged_users[socket_connection_ip])
	if data is None:
		data = "[SERVER] Game Over - The Client already answered on all the questions in the DB ..."
		build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["no_questions_msg"], data)
	else:
		build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["your_question_msg"], data)


def handle_answer_message(socket_connection, user_name, data):
	"""
	Explanations: Check the answer of the client.

	Receives: socket_connection (socket object), user_name (str), data (str).

	Returns: None.
	"""
	global users
	global questions

	id_question, user_answer = data.split(chatlib.DATA_DELIMITER)

	if user_answer not in questions[int(id_question)]["answers"]:
		data = f'[SERVER] Wrong. You try to type answer that not related to the options ...'
		build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["wrong_answer_msg"], data)
	else:
		if int(user_answer) == questions[int(id_question)]["correct"]:
			users[user_name]["score"] += CORRECT_ANSWER_POINT
			data = f'[SERVER] Great, Correct Answer ...'
			build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["correct_answer_msg"], data)
		else:
			data = f'[SERVER] Wrong. The Correct Answer : {str(questions[int(id_question)]["correct"])}'
			build_and_send_message(socket_connection, chatlib.PROTOCOL_SERVER["wrong_answer_msg"], data)


def print_client_sockets(clients_sockets):
	"""
	Explanations: Print all clients sockets.

	Receives: clients_sockets (socket object).

	Returns: None.
	"""
	global logged_users

	for client_socket in clients_sockets:
		client_port, client_ip = client_socket.getpeername()
		print(f'{logged_users[client_ip]} : ({client_port} , {client_ip})')


def clean_current_socket(clients_sockets, socket_connection):
	"""
	Explanations: Remove all details of specific socket connection.

	Receives: clients_sockets (socket object), socket_connection (socket object).

	Returns: None.
	"""
	global logged_users

	print(f"Connection of {socket_connection} Closed ...")
	client_ip = socket_connection.getpeername()[1]
	del logged_users[client_ip]
	clients_sockets.remove(socket_connection)
	handle_logout_message(socket_connection)


# MAIN #
def main():
	# Initializes global users and questions dictionaries using load functions, will be used later #
	global users
	global questions
	global messages_to_send


	print("Welcome to Trivia Server !")
	questions       = load_questions_from_web()
	users           = load_user_database()
	server_socket   = setup_socket()
	clients_sockets = []

	while True:
		print("Waiting for new connection ...")

		ready_to_read, ready_to_write, in_error = select.select([server_socket] + clients_sockets, clients_sockets, [])
		for current_socket in ready_to_read:
			if current_socket is server_socket:
				(client_socket, client_address) = server_socket.accept()
				print(f'[SERVER] New Client {client_address} Joined ...')
				clients_sockets.append(client_socket)
			else:
				print(f"[SERVER] New Data From Existing Client {current_socket} ...")
				try:
					client_cmd, client_data = recv_message_and_parse(current_socket)
				except (socket.error, KeyboardInterrupt, OSError):
					clean_current_socket(clients_sockets, current_socket)
				else:
					"""
					Explanations :
					client_cmd == ""                                    : It Means that the Client Press on Ctrl + C.
					client_cmd == chatlib.PROTOCOL_CLIENT["logout_msg"] : It Means that the Client sent Logout Message.
					client_cmd == chatlib.ERROR_RETURN                  : It Means that there is error / issue in connection between Client and Server.
					"""
					if client_cmd == "" or client_cmd == chatlib.PROTOCOL_CLIENT["logout_msg"] or client_cmd == chatlib.ERROR_RETURN:
						clean_current_socket(clients_sockets, current_socket)
					else:
						handle_client_message(current_socket, client_cmd, client_data)

						for message in messages_to_send:
							socket_to_send, data_to_send = message
							if socket_to_send in ready_to_write:
								socket_to_send.send(data_to_send.encode())
								messages_to_send.remove(message)


if __name__ == '__main__':
	main()
