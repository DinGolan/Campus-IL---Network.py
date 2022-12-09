# Protocol Constants #
CMD_FIELD_LENGTH    = 16	                                          # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4                                               # Exact length of length field (in bytes)
MAX_DATA_LENGTH     = 10 ** LENGTH_FIELD_LENGTH - 1                   # Max size of data field according to protocol
MSG_HEADER_LENGTH   = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH      = MSG_HEADER_LENGTH + MAX_DATA_LENGTH             # Max size of total message
DELIMITER           = "|"                                             # Delimiter character in protocol
DATA_DELIMITER      = "#"                                             # Delimiter in the data part of the message


# Protocol Messages #
PROTOCOL_CLIENT = {
"login_msg"        : "LOGIN",
"logout_msg"       : "LOGOUT",
"logged_msg"       : "LOGGED",
"get_question_msg" : "GET_QUESTION",
"send_answer_msg"  : "SEND_ANSWER",
"my_score_msg"     : "MY_SCORE",
"high_score_msg"   : "HIGHSCORE"
}


PROTOCOL_SERVER = {
"login_ok_msg"      : "LOGIN_OK",
"logged_answer_msg" : "LOGGED_ANSWER",
"your_question_msg" : "YOUR_QUESTION",
"correct_answer_msg": "CORRECT_ANSWER",
"wrong_answer_msg"  : "WRONG_ANSWER",
"your_score_msg"    : "YOUR_SCORE",
"all_score_msg"     : "ALL_SCORE",
"login_failed_msg"  : "ERROR",
"no_questions_msg"  : "NO_QUESTIONS"
}


# Other Constants
ERROR_RETURN = None


def build_message(cmd, data):
	"""
	Explanations: Gets command name (str) and data field (str) and creates a valid protocol message.

	Returns: str, or None if error occurred.
	"""
	if cmd not in PROTOCOL_CLIENT.values():
		return ERROR_RETURN

	full_msg = cmd + ((CMD_FIELD_LENGTH - len(cmd)) * ' ') + "|" + str(len(data)).zfill(LENGTH_FIELD_LENGTH) + "|" + data
	return full_msg


def parse_message(data):
	"""
	Explanations: Parses protocol message and returns command name and data field.

	Returns: cmd (str), data (str). If some error occurred, returns None, None.
	"""
	if data.count("|") != 2:
		return ERROR_RETURN, ERROR_RETURN

	cmd        = data.split("|")[0]
	msg_length = data.split("|")[1]
	msg        = data.split("|")[-1]

	try:
		if len(msg) != int(msg_length.strip()):
			return ERROR_RETURN, ERROR_RETURN

	except (ValueError, TypeError):
		return ERROR_RETURN, ERROR_RETURN

	return cmd.strip(), msg


def split_data(msg, expected_delimeters):
	"""
	Explanations: Helper method. gets a string and number of expected fields in it. Splits the string.
	using protocol's data field delimiter (|#) and validates that there are correct number of fields.

	Returns: list of fields if all ok. If some error occurred, returns None.
	"""
	msg_fields = msg.split(DELIMITER)[-1].strip()

	if msg_fields.count(DATA_DELIMITER) != expected_delimeters:
		return [ERROR_RETURN]

	return msg_fields.split(DATA_DELIMITER)


def join_data(msg_fields):
	"""
	Explanations: Helper method. Gets a list, joins all of its fields to one string divided by the data delimiter.

	Returns: string that looks like 'cell1#cell2#cell3'.
	"""
	msg_fields_str = []

	for field in msg_fields:
		if type(field) != str: msg_fields_str.append(str(field))
		else:                  msg_fields_str.append(field)

	return DATA_DELIMITER.join(msg_fields_str)
